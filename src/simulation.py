"""
Core simulation engine — world state, agent cognition, tick loop.
"""
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from .db import get_conn, _lock

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------
LOCATIONS: dict[str, dict] = {
    "fire_pit":   {"x": 10, "y": 10},
    "berry_bush": {"x": 3,  "y": 16},
    "shelter":    {"x": 17, "y": 3},
}
BERRY_REGEN  = 1
MAX_BERRIES  = 20
TICK_INTERVAL = int(os.getenv("TICK_INTERVAL", "5"))


# ------------------------------------------------------------------
# DB helpers
# ------------------------------------------------------------------
def _get_world() -> dict:
    conn = get_conn()
    row = conn.execute("SELECT * FROM world WHERE id=1").fetchone()
    conn.close()
    return dict(row)


def get_agents(alive_only: bool = True) -> list[dict]:
    conn = get_conn()
    q = "SELECT * FROM agents WHERE alive=1" if alive_only else "SELECT * FROM agents"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_recent_memories(agent_id: str, limit: int = 5) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT tick, event FROM memories WHERE agent_id=? ORDER BY tick DESC LIMIT ?",
        (agent_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_chronicle(limit: int = 30) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT tick, entry FROM chronicle ORDER BY tick DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return list(reversed([dict(r) for r in rows]))


def _add_memory(agent_id: str, tick: int, event: str) -> None:
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT INTO memories (agent_id, tick, event) VALUES (?, ?, ?)",
            (agent_id, tick, event),
        )
    conn.close()


def _add_chronicle(tick: int, entry: str, event_type: str = "AGENT_ACTION", agent_id: str = "SYSTEM") -> None:
    """Add an entry to the database chronicle and the file log."""
    conn = get_conn()
    with conn:
        conn.execute("INSERT INTO chronicle (tick, entry) VALUES (?, ?)", (tick, entry))
    conn.close()
    
    # Also log to file with detailed format
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] | [{tick}] | {event_type} | {agent_id} | {entry}\n"
    
    try:
        with open("chronicle.log", "a") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Warning: Could not write to chronicle.log: {e}")


def _log_to_file(tick: int, agents: list[dict], berry_count: int) -> None:
    """Append a tick summary to chronicle.log file."""
    alive_count = len([a for a in agents if a["alive"]])
    _add_chronicle(tick, f"Agents alive: {alive_count}, Berries: {berry_count}", "TICK_SUMMARY", "SYSTEM")



# ------------------------------------------------------------------
# Prompt builder
# ------------------------------------------------------------------
def _build_prompt(agent: dict, agents_at_loc: list[dict], berry_count: int) -> str:
    inventory = json.loads(agent["inventory"])
    memories  = _get_recent_memories(agent["id"])
    mem_text  = (
        "\n".join(f"- (Tick {m['tick']}) {m['event']}" for m in memories)
        or "None yet."
    )
    others = [a for a in agents_at_loc if a["id"] != agent["id"]]
    others_text = (
        ", ".join(f"{a['name']} (hunger:{a['hunger']}, energy:{a['energy']})" for a in others)
        or "Nobody else here."
    )

    return f"""You are {agent['name']}, an autonomous agent in The Grove.

TRAITS: Greed={agent['greed']:.1f}, Sociability={agent['sociability']:.1f}, Curiosity={agent['curiosity']:.1f}

STATE:
- Hunger:    {agent['hunger']}/10  (eat if below 4!)
- Energy:    {agent['energy']}/10  (sleep if below 2!)
- Community: {agent['community']}/10
- Location:  {agent['location']}
- Inventory: {inventory if inventory else 'empty'}

WHO IS HERE: {others_text}
BERRY BUSH:  {berry_count} berries available

RECENT MEMORIES:
{mem_text}

AVAILABLE ACTIONS:
  MOVE_TO    — target: "fire_pit" | "berry_bush" | "shelter"
  FORAGE     — (only at berry_bush, costs 1 energy, gives 2 berries)
  EAT        — consume 1 berry from inventory
  SLEEP      — (only at shelter, restores 4 energy)
  TALK       — target: agent name at same location, message: short speech
  GIVE_BERRY — target: agent name at same location
  DO_NOTHING

Respond ONLY with valid JSON:
{{"thought": "...", "action": "...", "target": "...", "message": "..."}}"""


# ------------------------------------------------------------------
# Action executor
# ------------------------------------------------------------------
def _apply_action(
    agent: dict,
    action_data: dict,
    agents: list[dict],
    berry_count: int,
    tick: int,
) -> None:
    inventory = json.loads(agent["inventory"])
    action  = str(action_data.get("action") or "DO_NOTHING").upper()
    target  = str(action_data.get("target") or "").strip().lower()
    message = str(action_data.get("message") or "").strip()

    conn = get_conn()
    try:
        # ---- MOVE_TO ----
        if action == "MOVE_TO" and target in LOCATIONS and agent["energy"] > 0:
            with conn:
                conn.execute(
                    "UPDATE agents SET location=? WHERE id=?",
                    (target, agent["id"]),
                )
            _add_memory(agent["id"], tick, f"Moved to {target}")
            _add_chronicle(tick, f"{agent['name']} walked to {target.replace('_',' ')}", "MOVE", agent['id'])

        # ---- FORAGE ----
        elif action == "FORAGE" and agent["location"] == "berry_bush" and agent["energy"] > 0:
            actual = min(2, berry_count)
            if actual > 0:
                inventory.extend(["berry"] * actual)
                with conn:
                    conn.execute(
                        "UPDATE agents SET inventory=?, energy=MAX(0,energy-1) WHERE id=?",
                        (json.dumps(inventory), agent["id"]),
                    )
                    conn.execute(
                        "UPDATE world SET berry_count=MAX(0,berry_count-?) WHERE id=1",
                        (actual,),
                    )
                _add_memory(agent["id"], tick, f"Foraged {actual} berries 🫐")
                _add_chronicle(tick, f"{agent['name']} foraged {actual} berries 🫐", "FORAGE", agent['id'])

        # ---- EAT ----
        elif action == "EAT" and "berry" in inventory:
            inventory.remove("berry")
            with conn:
                conn.execute(
                    "UPDATE agents SET inventory=?, hunger=MIN(10,hunger+3) WHERE id=?",
                    (json.dumps(inventory), agent["id"]),
                )
            _add_memory(agent["id"], tick, "Ate a berry — hunger relieved")
            _add_chronicle(tick, f"{agent['name']} is eating a berry 🫐", "EAT", agent['id'])

        # ---- SLEEP ---- (works anywhere when exhausted, best at shelter)
        elif action == "SLEEP" or (agent["energy"] == 0 and action != "EAT"):
            gain = 5 if agent["location"] == "shelter" else 2
            with conn:
                conn.execute(
                    "UPDATE agents SET energy=MIN(10,energy+?) WHERE id=?",
                    (gain, agent["id"]),
                )
            _add_memory(agent["id"], tick, f"Rested at {agent['location']} (+{gain} energy)")
            _add_chronicle(tick, f"{agent['name']} is sleeping/resting at {agent['location']}", "SLEEP", agent['id'])

        # ---- TALK ----
        elif action == "TALK" and target and message:
            tgt = next(
                (
                    a
                    for a in agents
                    if a["name"].lower() == target and a["location"] == agent["location"]
                ),
                None,
            )
            if tgt:
                with conn:
                    conn.execute(
                        "UPDATE agents SET community=MIN(10,community+2) WHERE id=?",
                        (agent["id"],),
                    )
                    conn.execute(
                        "UPDATE agents SET community=MIN(10,community+1) WHERE id=?",
                        (tgt["id"],),
                    )
                _add_memory(agent["id"], tick, f'Spoke to {tgt["name"]}: "{message[:60]}"')
                _add_memory(tgt["id"], tick, f'{agent["name"]} said: "{message[:60]}"')
                _add_chronicle(tick, f'💬 {agent["name"]} → {tgt["name"]}: "{message[:120]}"', "TALK", agent['id'])

        # ---- GIVE_BERRY ----
        elif action == "GIVE_BERRY" and "berry" in inventory and target:
            tgt = next(
                (
                    a
                    for a in agents
                    if a["name"].lower() == target and a["location"] == agent["location"]
                ),
                None,
            )
            if tgt:
                inventory.remove("berry")
                t_inv = json.loads(tgt["inventory"])
                t_inv.append("berry")
                with conn:
                    conn.execute(
                        "UPDATE agents SET inventory=? WHERE id=?",
                        (json.dumps(inventory), agent["id"]),
                    )
                    conn.execute(
                        "UPDATE agents SET inventory=? WHERE id=?",
                        (json.dumps(t_inv), tgt["id"]),
                    )
                _add_memory(agent["id"], tick, f'Gave a berry to {tgt["name"]}')
                _add_memory(tgt["id"], tick, f'{agent["name"]} gave me a berry 🎁')
                _add_chronicle(tick, f'🎁 {agent["name"]} gave a berry to {tgt["name"]}', "GIVE_BERRY", agent['id'])

    finally:
        conn.close()


# ------------------------------------------------------------------
# Main tick
# ------------------------------------------------------------------
def tick() -> int:
    """Advance the simulation by one tick. Uses parallel execution for agent thinking."""
    from .llm import call_llm

    world     = _get_world()
    new_tick  = world["tick"] + 1
    new_berry = min(MAX_BERRIES, world["berry_count"] + BERRY_REGEN)

    conn = get_conn()
    with conn:
        conn.execute(
            "UPDATE world SET tick=?, berry_count=? WHERE id=1",
            (new_tick, new_berry),
        )
    conn.close()

    agents  = get_agents()
    loc_map: dict[str, list[dict]] = {}
    for a in agents:
        loc_map.setdefault(a["location"], []).append(a)

    # 1. Prepare all agent prompts
    prompts = []
    for agent in agents:
        at_loc = loc_map.get(agent["location"], [])
        p = _build_prompt(agent, at_loc, new_berry)
        prompts.append((agent, p))

    # 2. Fire parallel LLM calls
    def _agent_think(pair: tuple[dict, str]) -> tuple[dict, dict]:
        agent, p = pair
        return agent, call_llm(p)

    with ThreadPoolExecutor(max_workers=len(agents) or 1) as executor:
        results = list(executor.map(_agent_think, prompts))

    # 3. Apply results sequentially (to maintain DB consistency)
    for agent, action_data in results:
        thought = (action_data.get("thought") or "")[:150]
        conn = get_conn()
        with conn:
            conn.execute(
                "UPDATE agents SET last_thought=? WHERE id=?",
                (thought, agent["id"]),
            )
        conn.close()

        _apply_action(agent, action_data, agents, new_berry, new_tick)

    # Natural decay
    conn = get_conn()
    with conn:
        conn.execute("UPDATE agents SET hunger=MAX(0,hunger-1) WHERE alive=1")
        conn.execute(
            "UPDATE agents SET energy=MAX(0,energy-1) WHERE alive=1 AND location!='shelter'"
        )
    conn.close()

    # Community loneliness decay
    alive = get_agents()
    for a in alive:
        companions = [x for x in alive if x["id"] != a["id"] and x["location"] == a["location"]]
        if not companions:
            conn = get_conn()
            with conn:
                conn.execute(
                    "UPDATE agents SET community=MAX(0,community-1) WHERE id=?",
                    (a["id"],),
                )
            conn.close()

    # Starvation check
    conn = get_conn()
    dead = conn.execute(
        "SELECT id, name FROM agents WHERE hunger=0 AND alive=1"
    ).fetchall()
    for d in dead:
        with conn:
            conn.execute("UPDATE agents SET alive=0 WHERE id=?", (d["id"],))
        _add_chronicle(new_tick, f"💀 {d['name']} has perished (starvation)", "DEATH", d["id"])
    conn.close()

    # Log tick summary to chronicle.log file
    alive_agents = get_agents()
    _log_to_file(new_tick, alive_agents, new_berry)

    return new_tick


# ------------------------------------------------------------------
# Agent management
# ------------------------------------------------------------------
def create_agent(name: str, greed: float, sociability: float, curiosity: float) -> str:
    agent_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    with conn:
        conn.execute(
            """INSERT INTO agents
               (id, name, greed, sociability, curiosity,
                hunger, energy, community, location, inventory,
                alive, created_tick, last_thought)
               VALUES (?, ?, ?, ?, ?, 8, 10, 6, 'fire_pit', '[]', 1,
                       (SELECT tick FROM world WHERE id=1), '')""",
            (agent_id, name, round(greed, 2), round(sociability, 2), round(curiosity, 2)),
        )
    conn.close()
    _add_chronicle(0, f"✨ {name} has entered The Grove", "SPAWN", agent_id)
    return agent_id


def seed_default_agents() -> None:
    """Populate the world with 3 starter agents if empty."""
    if not get_agents():
        create_agent("Ara",  greed=0.2, sociability=0.8, curiosity=0.5)
        create_agent("Dax",  greed=0.7, sociability=0.5, curiosity=0.8)
        create_agent("Mira", greed=0.1, sociability=0.9, curiosity=0.3)


# ------------------------------------------------------------------
# State serialisation
# ------------------------------------------------------------------
def get_state_dict() -> dict:
    world     = _get_world()
    agents    = get_agents(alive_only=False)
    chronicle = get_chronicle(limit=40)

    return {
        "tick":        world["tick"],
        "berry_count": world["berry_count"],
        "agents": [
            {
                "id":          a["id"],
                "name":        a["name"],
                "greed":       a["greed"],
                "sociability": a["sociability"],
                "curiosity":   a["curiosity"],
                "hunger":      a["hunger"],
                "energy":      a["energy"],
                "community":   a["community"],
                "location":    a["location"],
                "inventory":   json.loads(a["inventory"]),
                "alive":       bool(a["alive"]),
                "last_thought": a["last_thought"],
                "x":           LOCATIONS.get(a["location"], {}).get("x", 10),
                "y":           LOCATIONS.get(a["location"], {}).get("y", 10),
            }
            for a in agents
        ],
        "chronicle":  chronicle,
        "locations":  LOCATIONS,
    }
