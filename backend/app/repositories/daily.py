import sqlite3


def get(conn: sqlite3.Connection, date: str) -> str | None:
    row = conn.execute("select puzzle_id from daily where date = ?", (date,)).fetchone()
    return row["puzzle_id"] if row else None


def set(conn: sqlite3.Connection, date: str, puzzle_id: str) -> None:
    conn.execute("insert into daily (date, puzzle_id) values (?, ?) "
                 "on conflict(date) do update set puzzle_id = excluded.puzzle_id", (date, puzzle_id))
    conn.commit()


def history(conn: sqlite3.Connection) -> dict[str, str]:
    return {r["date"]: r["puzzle_id"] for r in conn.execute("select date, puzzle_id from daily order by date")}
