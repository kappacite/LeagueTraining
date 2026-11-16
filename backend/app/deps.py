"""FastAPI dependencies. Tests override get_now and get_http."""
import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime

import httpx
from fastapi import Depends, HTTPException, Request

from .config import Settings
from .db import connect
from .ddragon import DDragon
from .puzzles.loader import Catalog
from .repositories import sessions, users
from .services.auth import hash_token


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_catalog(request: Request) -> Catalog:
    return request.app.state.catalog


def get_dd(request: Request) -> DDragon:
    return request.app.state.dd


def get_now() -> datetime:
    return datetime.now(UTC)


def get_http() -> Iterator[httpx.Client]:
    with httpx.Client(timeout=10) as c:
        yield c


def get_conn(settings: Settings = Depends(get_settings)) -> Iterator[sqlite3.Connection]:
    conn = connect(settings.db_path)
    try:
        yield conn
    finally:
        conn.close()


def current_user(request: Request, conn: sqlite3.Connection = Depends(get_conn),
                 now: datetime = Depends(get_now)) -> sqlite3.Row:
    token = request.cookies.get("session")
    uid = sessions.user_id_for(conn, hash_token(token), now) if token else None
    user = users.get(conn, uid) if uid else None
    if user is None:
        raise HTTPException(401, "not logged in")
    return user
