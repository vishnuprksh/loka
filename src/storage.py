"""
Storage abstraction layer.

All database interactions go through StorageBackend so the simulation and
skill logic never import sqlite3 or get_conn directly.  Swapping in a
different backend (Postgres, in-memory for tests, etc.) requires only
instantiating a different subclass.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .environment import Environment

from .db import get_conn
from .config import MAX_STAT_VALUE, MEMORY_WINDOW_LIMIT, CHRONICLE_LIMIT


class StorageBackend(ABC):
    """Abstract interface for all world-persistence operations."""

    # ---- Agents ----------------------------------------------------------------

    @abstractmethod
    def get_agents(self, alive_only: bool = True) -> list[dict]: ...

    @abstractmethod
    def update_agent(self, agent_id: str, **fields) -> None: ...

    @abstractmethod
    def create_agent(
        self,
        agent_id: str,
        name: str,
        greed: float,
        sociability: float,
        curiosity: float,
        empathy: float = 0.5,
        assertiveness: float = 0.5,
        money: int = 10,
        path: str = "survivor",
    ) -> None: ...

    # ---- Relationships ---------------------------------------------------------

    @abstractmethod
    def get_relationships(self, agent_id: str) -> dict[str, int]:
        """Return all relationships for an agent as {other_agent_id: score}."""
        ...

    @abstractmethod
    def update_relationship(self, agent_a: str, agent_b: str, delta: int) -> None:
        """Add delta to the score agent_a has for agent_b (how B feels about A)."""
        ...

    @abstractmethod
    def get_public_social_status(self, agent_id: str) -> int:
        """Return the average score others have for this agent."""
        ...

    # ---- World -----------------------------------------------------------------

    @abstractmethod
    def get_world(self) -> dict: ...

    @abstractmethod
    def update_world(self, **fields) -> None: ...

    # ---- Resources -------------------------------------------------------------

    @abstractmethod
    def get_resources(self) -> dict[str, int]:
        """Return current counts as {resource_name: count}."""
        ...

    @abstractmethod
    def adjust_resource(self, name: str, delta: int) -> None:
        """Add delta to resource count, clamped to [0, max_count]."""
        ...

    # ---- Memories --------------------------------------------------------------

    @abstractmethod
    def get_recent_memories(self, agent_id: str, limit: int = MEMORY_WINDOW_LIMIT) -> list[dict]: ...

    @abstractmethod
    def add_memory(
        self,
        agent_id: str,
        tick: int,
        event: str,
        target: str | None = None,
        message: str | None = None,
        is_unanswered: int = 0,
        location: str | None = None,
    ) -> None: ...

    # ---- Chronicle -------------------------------------------------------------

    @abstractmethod
    def get_chronicle(self, limit: int = CHRONICLE_LIMIT) -> list[dict]: ...

    @abstractmethod
    def add_chronicle(
        self,
        tick: int,
        entry: str,
        event_type: str = "AGENT_ACTION",
        agent_id: str = "SYSTEM",
    ) -> None: ...

    # ---- Bulk helpers ----------------------------------------------------------

    @abstractmethod
    def tick_decay(self) -> None:
        """Apply natural per-tick stat decay to all alive agents."""
        ...

    @abstractmethod
    def kill_starved_agents(self) -> list[dict]:
        """Mark agents with hunger=0 as dead; return their records."""
        ...

    @abstractmethod
    def get_conn(self):
        """Return a database connection."""
        ...


# ---------------------------------------------------------------------------


class SQLiteBackend(StorageBackend):
    """SQLite-backed storage implementation."""

    def get_conn(self):
        return get_conn()

    # ---- Agents ----------------------------------------------------------------

    def get_agents(self, alive_only: bool = True) -> list[dict]:
        conn = get_conn()
        q = "SELECT * FROM agents WHERE alive=1" if alive_only else "SELECT * FROM agents"
        rows = conn.execute(q).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_agent(self, agent_id: str, **fields) -> None:
        if not fields:
            return
        # Filter out community if it's passed (since we removed the column)
        fields.pop("community", None)
        if not fields:
            return
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values()) + [agent_id]
        conn = get_conn()
        with conn:
            conn.execute(f"UPDATE agents SET {set_clause} WHERE id=?", values)
        conn.close()

    def create_agent(
        self,
        agent_id: str,
        name: str,
        greed: float,
        sociability: float,
        curiosity: float,
        empathy: float = 0.5,
        assertiveness: float = 0.5,
        money: int = 10,
        path: str = "survivor",
    ) -> None:
        conn = get_conn()
        with conn:
            conn.execute(
                """INSERT INTO agents
                   (id, name, greed, sociability, curiosity, empathy, assertiveness, path,
                    money, hunger, energy, location, inventory,
                    alive, created_tick, last_thought)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'fire_pit', '[]', 1,
                           (SELECT tick FROM world WHERE id=1), '')""",
                (agent_id, name, round(greed, 2), round(sociability, 2), round(curiosity, 2), 
                 round(empathy, 2), round(assertiveness, 2), path, money,
                 MAX_STAT_VALUE, MAX_STAT_VALUE),
            )
        conn.close()

    # ---- Relationships ---------------------------------------------------------

    def get_relationships(self, agent_id: str) -> dict[str, int]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT agent_b, score FROM relationships WHERE agent_a=?", (agent_id,)
        ).fetchall()
        conn.close()
        return {r["agent_b"]: r["score"] for r in rows}

    def update_relationship(self, agent_a: str, agent_b: str, delta: int) -> None:
        """agent_a is the one performing the action, agent_b is the target.
        The score being updated is how agent_b feels about agent_a.
        """
        conn = get_conn()
        with conn:
            # Check if relationship exists
            exists = conn.execute(
                "SELECT 1 FROM relationships WHERE agent_a=? AND agent_b=?", (agent_b, agent_a)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO relationships (agent_a, agent_b, score) VALUES (?, ?, ?)",
                    (agent_b, agent_a, max(0, min(MAX_STAT_VALUE, 5 + delta))),
                )
            else:
                conn.execute(
                    "UPDATE relationships SET score=MAX(0, MIN(?, score+?)) WHERE agent_a=? AND agent_b=?",
                    (MAX_STAT_VALUE, delta, agent_b, agent_a),
                )
        conn.close()

    def get_public_social_status(self, agent_id: str) -> int:
        conn = get_conn()
        row = conn.execute(
            "SELECT AVG(score) FROM relationships WHERE agent_b=?", (agent_id,)
        ).fetchone()
        conn.close()
        # Default to 5 if no relationships
        return int(row[0]) if row and row[0] is not None else 5

    # ---- World -----------------------------------------------------------------

    def get_world(self) -> dict:
        conn = get_conn()
        row = conn.execute("SELECT * FROM world WHERE id=1").fetchone()
        conn.close()
        return dict(row)

    def update_world(self, **fields) -> None:
        if not fields:
            return
        set_clause = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values())
        conn = get_conn()
        with conn:
            conn.execute(f"UPDATE world SET {set_clause} WHERE id=1", values)
        conn.close()

    # ---- Resources -------------------------------------------------------------

    def get_resources(self) -> dict[str, int]:
        conn = get_conn()
        rows = conn.execute("SELECT name, count FROM world_resources").fetchall()
        conn.close()
        return {r["name"]: r["count"] for r in rows}

    def adjust_resource(self, name: str, delta: int) -> None:
        conn = get_conn()
        with conn:
            conn.execute(
                "UPDATE world_resources SET count=MAX(0, MIN(max_count, count+?)) WHERE name=?",
                (delta, name),
            )
        conn.close()

    # ---- Memories --------------------------------------------------------------

    def get_recent_memories(self, agent_id: str, limit: int = MEMORY_WINDOW_LIMIT) -> list[dict]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT tick, event, target, message, is_unanswered, location FROM memories "
            "WHERE agent_id=? ORDER BY tick DESC LIMIT ?",
            (agent_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add_memory(
        self,
        agent_id: str,
        tick: int,
        event: str,
        target: str | None = None,
        message: str | None = None,
        is_unanswered: int = 0,
        location: str | None = None,
    ) -> None:
        conn = get_conn()
        with conn:
            conn.execute(
                "INSERT INTO memories (agent_id, tick, event, target, message, is_unanswered, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (agent_id, tick, event, target, message, is_unanswered, location),
            )
        conn.close()

    # ---- Chronicle -------------------------------------------------------------

    def get_chronicle(self, limit: int = CHRONICLE_LIMIT) -> list[dict]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT tick, entry FROM chronicle ORDER BY tick DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return list(reversed([dict(r) for r in rows]))

    def add_chronicle(
        self,
        tick: int,
        entry: str,
        event_type: str = "AGENT_ACTION",
        agent_id: str = "SYSTEM",
    ) -> None:
        conn = get_conn()
        with conn:
            conn.execute("INSERT INTO chronicle (tick, entry) VALUES (?, ?)", (tick, entry))
        conn.close()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] | [{tick}] | {event_type} | {agent_id} | {entry}\n"
        try:
            with open("chronicle.log", "a") as f:
                f.write(log_line)
        except Exception as e:
            print(f"Warning: Could not write to chronicle.log: {e}")

    # ---- Bulk helpers ----------------------------------------------------------

    def tick_decay(self) -> None:
        conn = get_conn()
        with conn:
            # Stats decay by 1 EVERY tick as requested
            conn.execute("UPDATE agents SET hunger=MAX(0,hunger-1) WHERE alive=1")
            conn.execute(
                "UPDATE agents SET energy=MAX(0,energy-1) WHERE alive=1 AND location!='shelter' AND location!='fire_pit'"
            )

        conn.close()

    def kill_starved_agents(self) -> list[dict]:
        conn = get_conn()
        dead = conn.execute(
            "SELECT id, name FROM agents WHERE hunger=0 AND alive=1"
        ).fetchall()
        dead_list = [dict(d) for d in dead]
        with conn:
            for d in dead_list:
                conn.execute("UPDATE agents SET alive=0 WHERE id=?", (d["id"],))
        conn.close()
        return dead_list
