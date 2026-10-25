import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).with_name("smartsign_history.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phrase TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    return conn


def add_message(phrase, source):
    text = (phrase or "").strip()
    if not text:
        return
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO messages (phrase, source, created_at) VALUES (?, ?, ?)",
                (text, source, datetime.now().isoformat(timespec="seconds")),
            )
    except sqlite3.Error as exc:
        print(f"History database error: {exc}")


def get_recent_messages(limit=8):
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT phrase, source, created_at FROM messages ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"phrase": row[0], "source": row[1], "created_at": row[2]} for row in rows
        ]
    except sqlite3.Error as exc:
        print(f"History database error: {exc}")
        return []
