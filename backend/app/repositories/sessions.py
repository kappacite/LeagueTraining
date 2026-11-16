import sqlite3
from datetime import datetime


def create(conn: sqlite3.Connection, token_hash: str, user_id: int, expires_at: datetime) -> None:
    conn.execute("insert into sessions (token_hash, user_id, expires_at) values (?, ?, ?)",
                 (token_hash, user_id, expires_at.isoformat()))
    conn.commit()


def user_id_for(conn: sqlite3.Connection, token_hash: str, now: datetime) -> int | None:
    row = conn.execute("select user_id from sessions where token_hash = ? and expires_at > ?",
                       (token_hash, now.isoformat())).fetchone()
    return row["user_id"] if row else None


def delete(conn: sqlite3.Connection, token_hash: str) -> None:
    conn.execute("delete from sessions where token_hash = ?", (token_hash,))
    conn.commit()
