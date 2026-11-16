import secrets
import sqlite3
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from ..config import Settings
from ..deps import current_user, get_conn, get_http, get_now, get_settings
from ..repositories import sessions
from ..services import auth
from ..views import user_public

router = APIRouter()
OAUTH_COOKIE = "oauth"


def _cookie(response: Response, name: str, value: str, max_age: int) -> None:
    response.set_cookie(name, value, max_age=max_age, httponly=True, secure=True, samesite="lax", path="/")


@router.get("/api/auth/login")
def login(settings: Settings = Depends(get_settings)):
    state, verifier = secrets.token_urlsafe(16), secrets.token_urlsafe(48)
    response = RedirectResponse(auth.authorize_url(settings, state, auth.pkce_challenge(verifier)), 302)
    _cookie(response, OAUTH_COOKIE, f"{state}.{verifier}", 600)
    return response


@router.get("/api/auth/callback")
def callback(request: Request, code: str, state: str, settings: Settings = Depends(get_settings),
             conn: sqlite3.Connection = Depends(get_conn), http: httpx.Client = Depends(get_http),
             now: datetime = Depends(get_now)):
    expected_state, _, verifier = request.cookies.get(OAUTH_COOKIE, "").partition(".")
    if not expected_state or not secrets.compare_digest(expected_state, state):
        raise HTTPException(400, "invalid oauth state")
    try:
        token = auth.login(conn, auth.fetch_discord_user(http, settings, code, verifier), now, settings.session_days)
    except auth.NotAllowed:
        response = RedirectResponse("/#/login?error=not-allowed", 302)
    except httpx.HTTPError:
        response = RedirectResponse("/#/login?error=discord", 302)
    else:
        response = RedirectResponse("/#/", 302)
        _cookie(response, "session", token, settings.session_days * 86400)
    response.delete_cookie(OAUTH_COOKIE, path="/")
    return response


@router.post("/api/auth/logout", status_code=204)
def logout(request: Request, conn: sqlite3.Connection = Depends(get_conn)):
    token = request.cookies.get("session")
    if token:
        sessions.delete(conn, auth.hash_token(token))
    response = Response(status_code=204)
    response.delete_cookie("session", path="/")
    return response


@router.get("/api/me")
def me(user=Depends(current_user)):
    return user_public(user)
