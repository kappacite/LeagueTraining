import sqlite3
from datetime import datetime


def is_allowed(conn: sqlite3.Connection, discord_id: str) -> bool:
    return conn.execute("select 1 from allowlist where discord_id = ?", (discord_id,)).fetchone() is not None


def add(conn: sqlite3.Connection, discord_id: str, now: datetime) -> None:
    conn.execute("insert or ignore into allowlist (discord_id, added_at) values (?, ?)", (discord_id, now.isoformat()))
    conn.commit()


def remove(conn: sqlite3.Connection, discord_id: str) -> None:
    """Revoking access also kills the user's live sessions."""
    conn.execute("delete from allowlist where discord_id = ?", (discord_id,))
    conn.execute("delete from sessions where user_id in (select id from users where discord_id = ?)", (discord_id,))
    conn.commit()


def all(conn: sqlite3.Connection) -> list[str]:
    return [r["discord_id"] for r in conn.execute("select discord_id from allowlist order by added_at, discord_id")]
