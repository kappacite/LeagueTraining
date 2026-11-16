import base64
import hashlib
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx

from ..config import Settings
from ..repositories import allowlist, sessions, users

AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
ME_URL = "https://discord.com/api/users/@me"


class NotAllowed(Exception):
    pass


@dataclass
class DiscordUser:
    id: str
    name: str
    avatar: str | None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_session(conn: sqlite3.Connection, user_id: int, now: datetime, days: int) -> str:
    token = secrets.token_urlsafe(32)
    sessions.create(conn, hash_token(token), user_id, now + timedelta(days=days))
    return token


def pkce_challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def authorize_url(settings: Settings, state: str, code_challenge: str) -> str:
    return AUTHORIZE_URL + "?" + urlencode({
        "client_id": settings.discord_client_id,
        "redirect_uri": settings.discord_redirect_uri,
        "response_type": "code",
        "scope": "identify",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })


def fetch_discord_user(client: httpx.Client, settings: Settings, code: str, verifier: str) -> DiscordUser:
    r = client.post(TOKEN_URL, data={
        "client_id": settings.discord_client_id,
        "client_secret": settings.discord_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.discord_redirect_uri,
        "code_verifier": verifier,
    })
    r.raise_for_status()
    me = client.get(ME_URL, headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    me.raise_for_status()
    u = me.json()
    return DiscordUser(id=str(u["id"]), name=u.get("global_name") or u["username"], avatar=u.get("avatar"))


def login(conn: sqlite3.Connection, du: DiscordUser, now: datetime, days: int) -> str:
    if not allowlist.is_allowed(conn, du.id):
        raise NotAllowed(du.id)
    return new_session(conn, users.upsert(conn, du.id, du.name, du.avatar, now), now, days)
