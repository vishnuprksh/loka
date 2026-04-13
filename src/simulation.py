"""
Core simulation engine — world state, agent cognition, tick loop.

Uses Environment, SkillRegistry, and StorageBackend so the tick loop
itself never needs to change when new locations, resources, or skills
are added.
"""
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

from .environment import THE_GROVE, Environment
from .skills import SKILL_REGISTRY, SkillRegistry
from .storage import SQLiteBackend, StorageBackend
from .config import (
    MAX_STAT_VALUE, HUNGER_THRESHOLD_LOW, ENERGY_THRESHOLD_LOW,
    MEMORY_WINDOW_LIMIT, DEFAULT_TICK_INTERVAL
)

TICK_INTERVAL = int(os.getenv("TICK_INTERVAL", str(DEFAULT_TICK_INTERVAL)))

# ---------------------------------------------------------------------------
# Module-level singletons.  Replace these in tests or alternative configs.
# ---------------------------------------------------------------------------
ENV: Environment = THE_GROVE
SKILLS: SkillRegistry = SKILL_REGISTRY
STORAGE: StorageBackend = SQLiteBackend()


# ------------------------------------------------------------------
# Prompt builder
# ------------------------------------------------------------------
def _build_prompt(agent: dict, agents_at_loc: list[dict], resource_state: dict[str, int]) -> str:
    inventory = json.loads(agent["inventory"])
    memories = STORAGE.get_recent_memories(agent["id"], limit=MEMORY_WINDOW_LIMIT)

    unanswered_message = None
    mem_lines = []
    for m in memories:
        status = ""
        if m.get("is_unanswered"):
            status = " [UNANSWERED]"
            unanswered_message = m["message"]
        
        if "said:" in m["event"] or "Spoke to" in m["event"]:
            line = f"- (Tick {m['tick']}) [SOCIAL]{status} {m['event']}"
        else:
            line = f"- (Tick {m['tick']}){status} {m['event']}"
        mem_lines.append(line)
    mem_text = "\n".join(mem_lines) or "None yet."

    others = [a for a in agents_at_loc if a["id"] != agent["id"]]
    others_text = (
        ", ".join(f"{a['name']} (hunger:{a['hunger']}, energy:{a['energy']})" for a in others)
        or "Nobody else here."
    )

    # Resource lines — built from environment, not hardcoded
    resource_lines = []
    for res in ENV.resources.values():
        count = resource_state.get(res.name, 0)
        harvest_locs = ", ".join(res.harvest_locations)
        resource_lines.append(
            f"{res.name.upper()} {res.icon}: {count} available (harvest at: {harvest_locs})"
        )
    resources_text = "\n".join(resource_lines) or "No resources."

    # Location and skill lists — built from environment and registry
    locations_text = " | ".join(f'"{loc}"' for loc in ENV.location_names())
    skill_lines_text = "\n  ".join(
        line.replace("MOVE_TO    — target: location name", f"MOVE_TO    — target: {locations_text}")
        for line in SKILLS.prompt_lines()
    )

    path_missions = {
        "Performer": "YOUR PATH: The Performer (Yellow). Survival through charm and social influence. Build community, entertain, and maintain enthusiasm to keep morale high.",
        "Scholar": "YOUR PATH: The Scholar (Blue). Survival through knowledge and precision. Observe patterns, analyze resources, and provide the group with systematic insights.",
        "Commoner": "YOUR PATH: The Commoner (Green). Survival through stability and harmony. Be reliable, support others, and ensure the community remains peaceful and steady.",
        "Leader": "YOUR PATH: The Leader (Red). Survival through decisive action and results. Take charge, prioritize efficiency, and lead the group toward clear objectives.",
    }
    path_instruction = path_missions.get(agent.get("path"), "YOUR PATH: The Survivor. Do what you must to stay alive.")

    mandatory_reply_instruction = ""
    if unanswered_message:
        mandatory_reply_instruction = f"\n\nCRITICAL: {unanswered_message} was just said to you. You MUST respond in this tick using the TALK action. After responding, decide if you wish to CONTINUE the conversation or END it."

    return f"""You are {agent['name']}, an autonomous agent in {ENV.name}.

TRAITS: Greed={agent['greed']:.1f}, Sociability={agent['sociability']:.1f}, Curiosity={agent['curiosity']:.1f}, Empathy={agent.get('empathy', 0.5):.1f}, Assertiveness={agent.get('assertiveness', 0.5):.1f}
PATH: {agent.get('path', 'Survivor')}

STATE:
- Hunger:    {agent['hunger']}/{MAX_STAT_VALUE}  (eat if below {HUNGER_THRESHOLD_LOW}! Low hunger makes you TIRED)
- Energy:    {agent['energy']}/{MAX_STAT_VALUE}  (sleep if below {ENERGY_THRESHOLD_LOW}! Low energy makes you HUNGRY)
- Community: {agent['community']}/{MAX_STAT_VALUE}
- Location:  {agent['location']}
- Inventory: {inventory if inventory else 'empty'}

WHO IS HERE: {others_text}

WORLD RESOURCES:
{resources_text}

RECENT MEMORIES (Most recent at top):
{mem_text}

MISSION: Survive and build a society. {path_instruction}{mandatory_reply_instruction}

AVAILABLE ACTIONS:
  {skill_lines_text}

Respond ONLY with valid JSON:
{{
  "thought": "...", 
  "action": "...", 
  "target": "...", 
  "message": "...",
  "conversation_status": "CONTINUE" or "END" (only relevant if you use TALK)
}}"""


# ------------------------------------------------------------------
# Action executor
# ------------------------------------------------------------------
def _apply_action(
    agent: dict,
    action_data: dict,
    agents: list[dict],
    resource_state: dict[str, int],
    tick: int,
) -> None:
    action = str(action_data.get("action") or "DO_NOTHING").upper()
    target = str(action_data.get("target") or "").strip().lower()
    message = str(action_data.get("message") or "").strip()

    # Force sleep when energy hits zero (regardless of chosen action)
    if agent["energy"] == 0 and action != "EAT":
        action = "SLEEP"
        target = ""
        message = ""

    skill = SKILLS.get(action)
    if skill and skill.validate(agent, target, message, agents, resource_state, ENV):
        skill.execute(agent, target, message, agents, resource_state, ENV, tick, STORAGE)


# ------------------------------------------------------------------
# Main tick
# ------------------------------------------------------------------
def tick() -> int:
    """Advance the simulation by one tick."""
    from .llm import call_llm

    world = STORAGE.get_world()
    new_tick = world["tick"] + 1
    STORAGE.update_world(tick=new_tick)

    # Regenerate all world resources (driven by Environment config)
    for res in ENV.resources.values():
        STORAGE.adjust_resource(res.name, res.regen_per_tick)

    resource_state = STORAGE.get_resources()
    agents = STORAGE.get_agents()

    loc_map: dict[str, list[dict]] = {}
    for a in agents:
        loc_map.setdefault(a["location"], []).append(a)

    # 1. Prepare all agent prompts
    prompts = [
        (agent, _build_prompt(agent, loc_map.get(agent["location"], []), resource_state))
        for agent in agents
    ]

    # 2. Fire parallel LLM calls
    def _agent_think(pair: tuple) -> tuple:
        agent, p = pair
        return agent, call_llm(p)

    with ThreadPoolExecutor(max_workers=len(agents) or 1) as executor:
        results = list(executor.map(_agent_think, prompts))

    # 3. Apply results sequentially (maintains DB consistency)
    for agent, action_data in results:
        thought = (action_data.get("thought") or "")[:150]
        STORAGE.update_agent(agent["id"], last_thought=thought)
        
        # If the action isn't TALK, or if conversation_status is END, clear unanswered for this agent
        # (Already partially handled in TalkSkill, but this ensures a "non-TALK" action clears the flag)
        if action_data.get("action") != "TALK" or action_data.get("conversation_status") == "END":
            conn = STORAGE.get_conn()
            with conn:
                conn.execute("UPDATE memories SET is_unanswered=0 WHERE agent_id=?", (agent["id"],))
            conn.close()

        _apply_action(agent, action_data, agents, resource_state, new_tick)

    # Natural stat decay
    STORAGE.tick_decay()

    # Community loneliness decay
    alive = STORAGE.get_agents()
    for a in alive:
        companions = [x for x in alive if x["id"] != a["id"] and x["location"] == a["location"]]
        if not companions:
            STORAGE.update_agent(a["id"], community=max(0, a["community"] - 1))

    # Starvation check
    dead_list = STORAGE.kill_starved_agents()
    for d in dead_list:
        STORAGE.add_chronicle(new_tick, f"💀 {d['name']} has perished (starvation)", "DEATH", d["id"])

    # Tick summary log
    alive_agents = STORAGE.get_agents()
    STORAGE.add_chronicle(
        new_tick,
        f"Agents alive: {len(alive_agents)}, Resources: {resource_state}",
        "TICK_SUMMARY",
        "SYSTEM",
    )

    return new_tick


# ------------------------------------------------------------------
# Agent management
# ------------------------------------------------------------------
def create_agent(name: str, greed: float, sociability: float, curiosity: float, 
                 empathy: float = 0.5, assertiveness: float = 0.5, path: str = None) -> str:
    agent_id = str(uuid.uuid4())[:8]

    # Determine path based on 4-color model if not provided
    if not path:
        traits = {
            "Performer": sociability,   # Yellow
            "Scholar": curiosity,       # Blue
            "Commoner": empathy,         # Green
            "Leader": assertiveness,     # Red
        }
        path = max(traits, key=traits.get)

    STORAGE.create_agent(agent_id, name, greed, sociability, curiosity, empathy, assertiveness, path=path)
    world = STORAGE.get_world()
    STORAGE.add_chronicle(world["tick"], f"✨ {name} ({path}) has entered {ENV.name}", "SPAWN", agent_id)
    return agent_id


def seed_default_agents() -> None:
    """Populate the world with starter agents if empty."""
    if not STORAGE.get_agents():
        # Ara (Yellow - Performer): Sociable, Enthusiastic
        create_agent("Ara",  greed=0.3, sociability=0.9, curiosity=0.6, empathy=0.7, assertiveness=0.6, path="Performer")
        
        # Dax (Blue - Scholar): Precise, Analytical
        create_agent("Dax",  greed=0.5, sociability=0.3, curiosity=0.9, empathy=0.3, assertiveness=0.4, path="Scholar")
        
        # Mira (Green - Commoner): Reliable, Harmonious
        create_agent("Mira", greed=0.2, sociability=0.8, curiosity=0.4, empathy=0.9, assertiveness=0.3, path="Commoner")
        
        # Kael (Red - Leader): Decisive, Result-oriented
        create_agent("Kael", greed=0.9, sociability=0.5, curiosity=0.6, empathy=0.2, assertiveness=0.9, path="Leader")


# ------------------------------------------------------------------
# State serialisation
# ------------------------------------------------------------------
def get_state_dict() -> dict:
    world = STORAGE.get_world()
    agents = STORAGE.get_agents(alive_only=False)
    chronicle = STORAGE.get_chronicle(limit=40)
    resource_state = STORAGE.get_resources()

    return {
        "tick":        world["tick"],
        "berry_count": resource_state.get("berry", 0),  # backward-compat for frontend
        "resources":   resource_state,
        "agents": [
            {
                "id":           a["id"],
                "name":         a["name"],
                "path":         a["path"],
                "greed":        a["greed"],
                "sociability":  a["sociability"],
                "curiosity":    a["curiosity"],
                "empathy":      a.get("empathy", 0.5),
                "assertiveness": a.get("assertiveness", 0.5),
                "hunger":       a["hunger"],
                "energy":       a["energy"],
                "community":    a["community"],
                "location":     a["location"],
                "inventory":    json.loads(a["inventory"]),
                "alive":        bool(a["alive"]),
                "last_thought": a["last_thought"],
                "x":            ENV.locations[a["location"]].x if a["location"] in ENV.locations else 10,
                "y":            ENV.locations[a["location"]].y if a["location"] in ENV.locations else 10,
            }
            for a in agents
        ],
        "chronicle": chronicle,
        "locations": {name: {"x": loc.x, "y": loc.y} for name, loc in ENV.locations.items()},
    }

