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


def init_db() -> None:
    conn = get_conn()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id           TEXT    PRIMARY KEY,
                name         TEXT    NOT NULL,
                greed        REAL    NOT NULL DEFAULT 0.5,
                sociability  REAL    NOT NULL DEFAULT 0.5,
                curiosity    REAL    NOT NULL DEFAULT 0.5,
                hunger       INTEGER NOT NULL DEFAULT 5,
                energy       INTEGER NOT NULL DEFAULT 10,
                community    INTEGER NOT NULL DEFAULT 5,
                location     TEXT    NOT NULL DEFAULT 'fire_pit',
                inventory    TEXT    NOT NULL DEFAULT '[]',
                alive        INTEGER NOT NULL DEFAULT 1,
                created_tick INTEGER NOT NULL DEFAULT 0,
                last_thought TEXT    NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS memories (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT    NOT NULL,
                tick     INTEGER NOT NULL,
                event    TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chronicle (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                tick  INTEGER NOT NULL,
                entry TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS world (
                id          INTEGER PRIMARY KEY DEFAULT 1,
                tick        INTEGER NOT NULL DEFAULT 0,
                berry_count INTEGER NOT NULL DEFAULT 20
            );

            INSERT OR IGNORE INTO world (id, tick, berry_count) VALUES (1, 0, 20);
        """)
    conn.close()


def reset_db() -> None:
    """Clear all data and reinitialize the database."""
    conn = get_conn()
    with conn:
        conn.execute("DELETE FROM agents")
        conn.execute("DELETE FROM memories")
        conn.execute("DELETE FROM chronicle")
        conn.execute("UPDATE world SET tick=0, berry_count=20 WHERE id=1")
    conn.close()
