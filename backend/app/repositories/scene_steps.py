import sqlite3
from datetime import datetime

Row = sqlite3.Row


def create(conn: sqlite3.Connection, attempt_id: int, node_id: str, started_at: datetime) -> int:
    cur = conn.execute("insert into scene_steps (attempt_id, node_id, started_at) values (?, ?, ?)",
                       (attempt_id, node_id, started_at.isoformat()))
    conn.commit()
    return cur.lastrowid


def current(conn: sqlite3.Connection, attempt_id: int) -> Row | None:
    return conn.execute("select * from scene_steps where attempt_id = ? and answered_at is null "
                        "order by id desc limit 1", (attempt_id,)).fetchone()


def close(conn: sqlite3.Connection, step_id: int, choice_id: str, grade: str, points: int, timed_out: bool,
          answered_at: datetime) -> bool:
    """False if the step was already answered (concurrent double submit)."""
    cur = conn.execute("update scene_steps set choice_id = ?, grade = ?, points = ?, timed_out = ?, answered_at = ? "
                       "where id = ? and answered_at is null",
                       (choice_id, grade, points, int(timed_out), answered_at.isoformat(), step_id))
    conn.commit()
    return cur.rowcount == 1


def path(conn: sqlite3.Connection, attempt_id: int) -> list[Row]:
    return conn.execute("select * from scene_steps where attempt_id = ? and answered_at is not null order by id",
                        (attempt_id,)).fetchall()


def distribution(conn: sqlite3.Connection, puzzle_id: str, node_id: str) -> list[Row]:
    return conn.execute(
        "select a.user_id, u.discord_id, u.name, u.avatar, s.choice_id, s.grade from scene_steps s "
        "join attempts a on a.id = s.attempt_id join users u on u.id = a.user_id "
        "where a.puzzle_id = ? and s.node_id = ? and a.scored = 1 and s.answered_at is not null "
        "order by s.answered_at", (puzzle_id, node_id)).fetchall()
