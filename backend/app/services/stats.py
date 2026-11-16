import sqlite3
from typing import get_args

from ..puzzles.loader import Catalog
from ..puzzles.types.base import Difficulty, Role
from ..repositories import attempts, users
from ..views import user_public


def _known(rows, catalog: Catalog):
    ids = catalog.ids()
    return [r for r in rows if r["puzzle_id"] in ids]


def _ranking(conn: sqlite3.Connection, rows) -> list[dict]:
    board = {u["id"]: {**user_public(u), "user_id": u["id"], "points": 0, "answered": 0} for u in users.all(conn)}
    for r in rows:
        board[r["user_id"]]["points"] += r["points"]
        board[r["user_id"]]["answered"] += 1
    return sorted(board.values(), key=lambda b: (-b["points"], b["name"].lower()))


def leaderboard(conn: sqlite3.Connection, catalog: Catalog, daily_history: dict[str, str]) -> dict:
    rows = _known(attempts.scored_answered(conn), catalog)
    daily_rows = [r for r in rows if daily_history.get(r["answered_day"]) == r["puzzle_id"]]
    return {"general": _ranking(conn, rows), "daily": _ranking(conn, daily_rows)}


def profile(conn: sqlite3.Connection, catalog: Catalog, user_id: int) -> dict | None:
    user = users.get(conn, user_id)
    if user is None:
        return None
    empty = lambda: {"answered": 0, "excellent": 0, "points": 0}  # noqa: E731
    by_role = {r: empty() for r in get_args(Role)}
    by_difficulty = {d: empty() for d in get_args(Difficulty)}
    for r in _known(attempts.scored_answered(conn, user_id), catalog):
        p = catalog.get(r["puzzle_id"])
        for bucket in (by_role[p.role], by_difficulty[p.difficulty]):
            bucket["answered"] += 1
            bucket["excellent"] += r["grade"] == "excellent"
            bucket["points"] += r["points"]
    return {"user": user_public(user), "total_points": sum(b["points"] for b in by_role.values()),
            "by_role": by_role, "by_difficulty": by_difficulty}
