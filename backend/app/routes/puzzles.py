import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import Settings
from ..deps import current_user, get_catalog, get_conn, get_now, get_settings
from ..puzzles.loader import Catalog
from ..puzzles.types.base import Difficulty, Role
from ..repositories import attempts as attempts_repo
from ..services import attempts, scenes

router = APIRouter(prefix="/api/puzzles")


class StartBody(BaseModel):
    mode: attempts.Mode = "normal"


class AnswerBody(BaseModel):
    choice: str


def _is_scene(catalog: Catalog, puzzle_id: str) -> bool:
    p = catalog.get(puzzle_id)
    return p is not None and p.type == "scene"


def _http(fn):
    try:
        return fn()
    except attempts.PuzzleNotFound:
        raise HTTPException(404, "unknown puzzle")
    except attempts.NoOpenAttempt:
        raise HTTPException(409, "no open attempt; call /start first")
    except attempts.UnknownChoice:
        raise HTTPException(422, "unknown choice")


@router.get("")
def list_puzzles(role: Role | None = None, difficulty: Difficulty | None = None, type: str | None = None,
                 user=Depends(current_user), conn: sqlite3.Connection = Depends(get_conn),
                 catalog: Catalog = Depends(get_catalog)):
    done = {r["puzzle_id"]: r["grade"] for r in attempts_repo.scored_answered(conn, user["id"])}
    return [{**p.summary().model_dump(), "done": p.id in done, "grade": done.get(p.id),
             "stale": catalog.is_stale(p)}
            for p in catalog.filter(role=role, difficulty=difficulty, type=type)]


@router.post("/{puzzle_id}/start")
def start(puzzle_id: str, body: StartBody, user=Depends(current_user), conn: sqlite3.Connection = Depends(get_conn),
          catalog: Catalog = Depends(get_catalog), now: datetime = Depends(get_now),
          settings: Settings = Depends(get_settings)):
    if _is_scene(catalog, puzzle_id):
        return _http(lambda: scenes.start(conn, catalog, user["id"], puzzle_id, body.mode, now,
                                          ZoneInfo(settings.timezone)))
    return _http(lambda: attempts.start(conn, catalog, user["id"], puzzle_id, body.mode, now))


@router.post("/{puzzle_id}/answer")
def answer(puzzle_id: str, body: AnswerBody, user=Depends(current_user),
           conn: sqlite3.Connection = Depends(get_conn), catalog: Catalog = Depends(get_catalog),
           now: datetime = Depends(get_now), settings: Settings = Depends(get_settings)):
    service = scenes if _is_scene(catalog, puzzle_id) else attempts
    return _http(lambda: service.answer(conn, catalog, user["id"], puzzle_id, body.choice, now,
                                        settings.chrono_grace_s, ZoneInfo(settings.timezone)))
