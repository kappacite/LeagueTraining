import sqlite3
from datetime import datetime


def upsert(conn: sqlite3.Connection, discord_id: str, name: str, avatar: str | None, now: datetime) -> int:
    row = conn.execute(
        "insert into users (discord_id, name, avatar, created_at) values (?, ?, ?, ?) "
        "on conflict(discord_id) do update set name = excluded.name, avatar = excluded.avatar "
        "returning id",
        (discord_id, name, avatar, now.isoformat()),
    ).fetchone()
    conn.commit()
    return row["id"]


def get(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return conn.execute("select * from users where id = ?", (user_id,)).fetchone()


def all(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("select * from users order by id").fetchall()
