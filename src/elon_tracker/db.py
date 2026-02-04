import sqlite3
from pathlib import Path
from typing import Iterable, Mapping

SCHEMA = """
CREATE TABLE IF NOT EXISTS tweets (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    date TEXT NOT NULL,
    day TEXT NOT NULL,
    time TEXT NOT NULL,
    is_retweet INTEGER NOT NULL,
    is_quote INTEGER NOT NULL,
    text TEXT NOT NULL
);
"""


def ensure_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def upsert_tweets(conn: sqlite3.Connection, rows: Iterable[Mapping[str, object]]) -> int:
    payload = [
        (
            row["id"],
            row["created_at"],
            row["date"],
            row["day"],
            row["time"],
            int(row["is_retweet"]),
            int(row["is_quote"]),
            row["text"],
        )
        for row in rows
    ]
    if not payload:
        return 0
    conn.executemany(
        """
        INSERT INTO tweets (
            id, created_at, date, day, time, is_retweet, is_quote, text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            created_at=excluded.created_at,
            date=excluded.date,
            day=excluded.day,
            time=excluded.time,
            is_retweet=excluded.is_retweet,
            is_quote=excluded.is_quote,
            text=excluded.text
        """,
        payload,
    )
    conn.commit()
    return len(payload)


def load_tweets(conn: sqlite3.Connection):
    return conn.execute(
        """SELECT created_at, day, time FROM tweets"""
    ).fetchall()
