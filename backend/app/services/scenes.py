"""Progression through an animated scene: one scene_steps row per node revealed, one attempt per play."""
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from ..puzzles.loader import Catalog
from ..puzzles.types.scene import Clip, ScenePuzzle
from ..repositories import attempts, scene_steps
from ..views import user_public
from .attempts import MULTIPLIER, POINTS, NoOpenAttempt, UnknownChoice, get_puzzle

GRADE_ORDER = ["erreur", "correct", "excellent"]


def _clip(clip: Clip) -> list[dict]:
    return [kf.model_dump(exclude_none=True) for kf in clip]


def _node(p: ScenePuzzle, node_id: str, started_at: str) -> dict:
    node = p.public_node(node_id).model_dump(exclude_none=True)
    return {**node, "started_at": started_at}


def _abandon(conn: sqlite3.Connection, row, now: datetime, tz: ZoneInfo) -> None:
    attempts.close(conn, row["id"], None, "erreur", 0, False, now, now.astimezone(tz).date().isoformat())


def start(conn: sqlite3.Connection, catalog: Catalog, user_id: int, puzzle_id: str, mode: str, now: datetime,
          tz: ZoneInfo) -> dict:
    p = get_puzzle(catalog, puzzle_id)
    row = attempts.open_scored(conn, user_id, puzzle_id)
    if row is None and not attempts.has_scored(conn, user_id, puzzle_id):
        try:
            row = attempts.get(conn, attempts.create(conn, user_id, puzzle_id, mode, now, scored=True))
        except sqlite3.IntegrityError:  # concurrent start
            conn.rollback()
            row = attempts.open_scored(conn, user_id, puzzle_id)
    step = scene_steps.current(conn, row["id"]) if row is not None else None
    if row is not None and step is not None and step["node_id"] not in p.nodes:
        _abandon(conn, row, now, tz)  # the scene was edited under this play: it can't continue
        row = step = None
    if row is None:  # practice: always a fresh play in the requested mode
        row = attempts.get(conn, attempts.create(conn, user_id, puzzle_id, mode, now, scored=False))
    if step is None:
        sid = scene_steps.create(conn, row["id"], p.start, now)
        step = conn.execute("select * from scene_steps where id = ?", (sid,)).fetchone()
    return {"puzzle": p.public(stale=catalog.is_stale(p)).model_dump(), "mode": row["mode"],
            "scored": bool(row["scored"]), "started_at": row["started_at"],
            "step": _node(p, step["node_id"], step["started_at"])}


def answer(conn: sqlite3.Connection, catalog: Catalog, user_id: int, puzzle_id: str, choice_id: str,
           now: datetime, grace_s: float, tz: ZoneInfo) -> dict:
    p = get_puzzle(catalog, puzzle_id)
    row = attempts.open_scored(conn, user_id, puzzle_id) or attempts.open_practice(conn, user_id, puzzle_id)
    step = scene_steps.current(conn, row["id"]) if row is not None else None
    if step is None or step["node_id"] not in p.nodes:
        raise NoOpenAttempt(puzzle_id)
    node = p.nodes[step["node_id"]]
    choice = node.choice(choice_id)
    if choice is None:
        raise UnknownChoice(choice_id)

    elapsed = (now - datetime.fromisoformat(step["started_at"])).total_seconds()
    timed_out = row["mode"] == "chrono" and elapsed > node.time_limit + grace_s
    grade = "erreur" if timed_out else choice.grade
    scored = bool(row["scored"])
    points = POINTS[grade] * MULTIPLIER[p.difficulty] if scored else 0
    if not scene_steps.close(conn, step["id"], choice_id, grade, points, timed_out, now):
        raise NoOpenAttempt(puzzle_id)  # concurrent double submit

    result = {
        "grade": grade, "points": points, "timed_out": timed_out, "scored": scored,
        "choices": [c.model_dump(include={"id", "text", "grade", "explanation"}) for c in node.choices],
        "consequence": _clip(choice.consequence),
        "distribution": [{**user_public(d), "choice_id": d["choice_id"], "grade": d["grade"]}
                         for d in scene_steps.distribution(conn, puzzle_id, step["node_id"])],
    }
    if choice.next:
        scene_steps.create(conn, row["id"], choice.next, now)
        result["next"] = _node(p, choice.next, now.isoformat())
        return result

    steps = scene_steps.path(conn, row["id"])
    path = [(s["node_id"], s["choice_id"]) for s in steps]
    total = sum(s["points"] for s in steps)
    worst = min((s["grade"] for s in steps), key=GRADE_ORDER.index)
    attempts.close(conn, row["id"], choice.ending, worst, total, any(s["timed_out"] for s in steps), now,
                   now.astimezone(tz).date().isoformat())
    optimal = p.optimal_path()
    reached, best = choice.ending, p.ending_of(optimal)
    result["end"] = {
        "reached": {"id": reached, **p.endings[reached].model_dump(exclude_none=True)},
        "optimal": {"id": best, **p.endings[best].model_dump(exclude_none=True)},
        "path": [{"node_id": s["node_id"], "choice_id": s["choice_id"], "grade": s["grade"], "points": s["points"]}
                 for s in steps],
        "optimal_path": [{"node_id": n, "choice_id": c} for n, c in optimal],
        "replay": {"mine": [_clip(c) for c in p.clips_for(path)], "optimal": [_clip(c) for c in p.clips_for(optimal)]},
        "total_points": total,
        "lesson": p.lesson,
    }
    return result
