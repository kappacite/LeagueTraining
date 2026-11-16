import sqlite3
from datetime import datetime

Row = sqlite3.Row


def open_scored(conn: sqlite3.Connection, user_id: int, puzzle_id: str) -> Row | None:
    return conn.execute("select * from attempts where user_id = ? and puzzle_id = ? and scored = 1 "
                        "and answered_at is null", (user_id, puzzle_id)).fetchone()


def open_practice(conn: sqlite3.Connection, user_id: int, puzzle_id: str) -> Row | None:
    return conn.execute("select * from attempts where user_id = ? and puzzle_id = ? and scored = 0 "
                        "and answered_at is null order by id desc limit 1", (user_id, puzzle_id)).fetchone()


def has_scored(conn: sqlite3.Connection, user_id: int, puzzle_id: str) -> bool:
    return conn.execute("select 1 from attempts where user_id = ? and puzzle_id = ? and scored = 1",
                        (user_id, puzzle_id)).fetchone() is not None


def create(conn: sqlite3.Connection, user_id: int, puzzle_id: str, mode: str, started_at: datetime,
           scored: bool) -> int:
    cur = conn.execute("insert into attempts (user_id, puzzle_id, mode, started_at, scored) values (?, ?, ?, ?, ?)",
                       (user_id, puzzle_id, mode, started_at.isoformat(), int(scored)))
    conn.commit()
    return cur.lastrowid


def close(conn: sqlite3.Connection, attempt_id: int, choice_id: str, grade: str, points: int, timed_out: bool,
          answered_at: datetime, answered_day: str) -> None:
    conn.execute("update attempts set choice_id = ?, grade = ?, points = ?, timed_out = ?, answered_at = ?, "
                 "answered_day = ? where id = ?",
                 (choice_id, grade, points, int(timed_out), answered_at.isoformat(), answered_day, attempt_id))
    conn.commit()


def get(conn: sqlite3.Connection, attempt_id: int) -> Row:
    return conn.execute("select * from attempts where id = ?", (attempt_id,)).fetchone()


def distribution(conn: sqlite3.Connection, puzzle_id: str) -> list[Row]:
    return conn.execute(
        "select a.user_id, u.discord_id, u.name, u.avatar, a.choice_id, a.grade from attempts a "
        "join users u on u.id = a.user_id where a.puzzle_id = ? and a.scored = 1 and a.answered_at is not null "
        "order by a.answered_at", (puzzle_id,)).fetchall()


def done_by(conn: sqlite3.Connection, puzzle_id: str) -> list[Row]:
    return conn.execute(
        "select u.id, u.discord_id, u.name, u.avatar from attempts a join users u on u.id = a.user_id "
        "where a.puzzle_id = ? and a.scored = 1 and a.answered_at is not null order by a.answered_at",
        (puzzle_id,)).fetchall()


def scored_answered(conn: sqlite3.Connection, user_id: int | None = None) -> list[Row]:
    sql = ("select user_id, puzzle_id, grade, points, answered_day from attempts "
           "where scored = 1 and answered_at is not null")
    if user_id is None:
        return conn.execute(sql + " order by id").fetchall()
    return conn.execute(sql + " and user_id = ? order by id", (user_id,)).fetchall()
