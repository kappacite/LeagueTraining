import random
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings
from ..deps import current_user, get_catalog, get_conn, get_now, get_settings
from ..puzzles.loader import Catalog
from ..repositories import attempts, daily as daily_repo
from ..services import daily, stats
from ..views import user_public

router = APIRouter(prefix="/api", dependencies=[Depends(current_user)])


@router.get("/daily")
def get_daily(conn: sqlite3.Connection = Depends(get_conn), catalog: Catalog = Depends(get_catalog),
              now: datetime = Depends(get_now), settings: Settings = Depends(get_settings)):
    tz = ZoneInfo(settings.timezone)
    p = daily.today(conn, catalog, now, tz, random.Random())
    return {"date": now.astimezone(tz).date().isoformat(), "puzzle": p.summary(),
            "done_by": [user_public(u) for u in attempts.done_by(conn, p.id)]}


@router.get("/leaderboard")
def get_leaderboard(conn: sqlite3.Connection = Depends(get_conn), catalog: Catalog = Depends(get_catalog)):
    return stats.leaderboard(conn, catalog, daily_repo.history(conn))


@router.get("/users/{user_id}")
def get_profile(user_id: int, conn: sqlite3.Connection = Depends(get_conn), catalog: Catalog = Depends(get_catalog)):
    p = stats.profile(conn, catalog, user_id)
    if p is None:
        raise HTTPException(404, "unknown user")
    return p
