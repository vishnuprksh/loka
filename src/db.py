import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "loka.db"
_lock = threading.RLock()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(env=None) -> None:
    """Create tables and seed resources from the given Environment.

    Passing env=None skips resource seeding (useful for bare-schema creation).
    Existing data is preserved; call reset_db() first for a fresh start.
    """
    conn = get_conn()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id           TEXT    PRIMARY KEY,
                name         TEXT    NOT NULL,
                greed        REAL    NOT NULL DEFAULT 0.5,
                sociability  REAL    NOT NULL DEFAULT 0.5,
                curiosity    REAL    NOT NULL DEFAULT 0.5,
                empathy      REAL    NOT NULL DEFAULT 0.5,
                assertiveness REAL    NOT NULL DEFAULT 0.5,
                hunger       INTEGER NOT NULL DEFAULT 5,
                energy       INTEGER NOT NULL DEFAULT 10,
                community    INTEGER NOT NULL DEFAULT 5,
                location     TEXT    NOT NULL DEFAULT 'fire_pit',
                inventory    TEXT    NOT NULL DEFAULT '[]',
                alive        INTEGER NOT NULL DEFAULT 1,
                path         TEXT    NOT NULL DEFAULT 'survivor',
                created_tick INTEGER NOT NULL DEFAULT 0,
                last_thought TEXT    NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS memories (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id     TEXT    NOT NULL,
                tick         INTEGER NOT NULL,
                event        TEXT    NOT NULL,
                target       TEXT,
                message      TEXT,
                is_unanswered INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS chronicle (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                tick  INTEGER NOT NULL,
                entry TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS world (
                id   INTEGER PRIMARY KEY DEFAULT 1,
                tick INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS world_resources (
                name      TEXT    PRIMARY KEY,
                count     INTEGER NOT NULL DEFAULT 0,
                max_count INTEGER NOT NULL DEFAULT 0
            );

            INSERT OR IGNORE INTO world (id, tick) VALUES (1, 0);
        """)

        # Seed resources from the environment definition
        if env is not None:
            for res in env.resources.values():
                conn.execute(
                    "INSERT OR IGNORE INTO world_resources (name, count, max_count) VALUES (?, ?, ?)",
                    (res.name, res.max_count, res.max_count),
                )
    conn.close()


def reset_db(env=None) -> None:
    """Clear all simulation data and re-seed resources from env."""
    # Ensure tables exist before truncating (handles first-run / schema migration)
    init_db(env)
    conn = get_conn()
    with conn:
        conn.execute("DELETE FROM agents")
        conn.execute("DELETE FROM memories")
        conn.execute("DELETE FROM chronicle")
        conn.execute("UPDATE world SET tick=0 WHERE id=1")
        conn.execute("DELETE FROM world_resources")
    conn.close()
    # Re-seed resource counts from environment
    if env is not None:
        conn = get_conn()
        with conn:
            for res in env.resources.values():
                conn.execute(
                    "INSERT OR IGNORE INTO world_resources (name, count, max_count) VALUES (?, ?, ?)",
                    (res.name, res.max_count, res.max_count),
                )
        conn.close()
