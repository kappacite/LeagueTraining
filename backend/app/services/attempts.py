import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from ..puzzles.loader import Catalog
from ..puzzles.types.base import Choice
from ..repositories import attempts
from ..views import user_public

POINTS = {"excellent": 3, "correct": 1, "erreur": 0}
MULTIPLIER = {"facile": 1, "moyen": 2, "difficile": 3}
Mode = Literal["normal", "chrono"]


class PuzzleNotFound(Exception):
    pass


class NoOpenAttempt(Exception):
    pass


class UnknownChoice(Exception):
    pass


@dataclass
class StartResult:
    puzzle: object  # PublicPuzzle
    mode: Mode
    started_at: datetime
    scored: bool


@dataclass
class AnswerResult:
    grade: str
    points: int
    timed_out: bool
    scored: bool
    choices: list[Choice]
    lesson: str
    distribution: list[dict]


def _puzzle(catalog: Catalog, puzzle_id: str):
    p = catalog.get(puzzle_id)
    if p is None:
        raise PuzzleNotFound(puzzle_id)
    return p


def start(conn: sqlite3.Connection, catalog: Catalog, user_id: int, puzzle_id: str, mode: Mode,
          now: datetime) -> StartResult:
    p = _puzzle(catalog, puzzle_id)
    # An open scored attempt is returned as-is: restarting must not reset the chrono or change the mode.
    row = attempts.open_scored(conn, user_id, puzzle_id)
    if row is None and not attempts.has_scored(conn, user_id, puzzle_id):
        try:
            row = attempts.get(conn, attempts.create(conn, user_id, puzzle_id, mode, now, scored=True))
        except sqlite3.IntegrityError:  # a concurrent request (double click, two tabs) created it first
            conn.rollback()
            row = attempts.open_scored(conn, user_id, puzzle_id)
    if row is None:
        # Practice attempts are unscored: always fresh, in the requested mode.
        row = attempts.get(conn, attempts.create(conn, user_id, puzzle_id, mode, now, scored=False))
    return StartResult(puzzle=p.public(stale=catalog.is_stale(p)), mode=row["mode"],
                       started_at=datetime.fromisoformat(row["started_at"]), scored=bool(row["scored"]))


def answer(conn: sqlite3.Connection, catalog: Catalog, user_id: int, puzzle_id: str, choice_id: str,
           now: datetime, grace_s: float, tz: ZoneInfo) -> AnswerResult:
    p = _puzzle(catalog, puzzle_id)
    row = attempts.open_scored(conn, user_id, puzzle_id) or attempts.open_practice(conn, user_id, puzzle_id)
    if row is None:
        raise NoOpenAttempt(puzzle_id)
    choice = p.grade(choice_id)
    if choice is None:
        raise UnknownChoice(choice_id)
    elapsed = (now - datetime.fromisoformat(row["started_at"])).total_seconds()
    timed_out = row["mode"] == "chrono" and elapsed > p.time_limit + grace_s
    grade = "erreur" if timed_out else choice.grade
    scored = bool(row["scored"])
    points = POINTS[grade] * MULTIPLIER[p.difficulty] if scored else 0
    attempts.close(conn, row["id"], choice_id, grade, points, timed_out, now, now.astimezone(tz).date().isoformat())
    distribution = [{**user_public(d), "choice_id": d["choice_id"], "grade": d["grade"]}
                    for d in attempts.distribution(conn, puzzle_id)]
    return AnswerResult(grade=grade, points=points, timed_out=timed_out, scored=scored, choices=p.choices,
                        lesson=p.lesson, distribution=distribution)
