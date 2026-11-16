from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import connect, migrate
from app.ddragon import load as load_ddragon
from app.deps import get_http, get_now
from app.puzzles.loader import load_catalog
from app.repositories import allowlist, users
from app.services.auth import new_session

FIXTURES = Path(__file__).parent / "fixtures"
ORIGIN = "https://lol.test"
T0 = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path, puzzles_dir=FIXTURES / "puzzles", static_dir=tmp_path / "static",
                    discord_client_id="cid", discord_client_secret="secret", public_origin=ORIGIN)


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "app.db")  # same file as settings.db_path
    migrate(c)
    yield c
    c.close()


@pytest.fixture
def dd():
    return load_ddragon(FIXTURES / "ddragon")


class Clock:
    def __init__(self):
        self.now = T0

    def advance(self, **kw):
        self.now += timedelta(**kw)


@pytest.fixture
def clock():
    return Clock()


class FakeDiscord:
    """Answers the two Discord endpoints the OAuth flow calls."""
    def __init__(self):
        self.user = {"id": "1001", "username": "faker", "global_name": "Faker", "avatar": "abc"}
        self.token_requests = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/oauth2/token":
            self.token_requests.append(dict(httpx.QueryParams(request.content.decode())))
            return httpx.Response(200, json={"access_token": "tok", "token_type": "Bearer"})
        if request.url.path == "/api/users/@me":
            return httpx.Response(200, json=self.user)
        return httpx.Response(404)


@pytest.fixture
def discord():
    return FakeDiscord()


@pytest.fixture
def app(settings, dd, clock, discord, conn):
    from app.main import create_app
    a = create_app(settings, dd=dd, catalog=load_catalog(settings.puzzles_dir, dd))
    a.dependency_overrides[get_now] = lambda: clock.now
    a.dependency_overrides[get_http] = lambda: httpx.Client(transport=httpx.MockTransport(discord))
    return a


@pytest.fixture
def client(app):
    with TestClient(app, base_url=ORIGIN, headers={"Origin": ORIGIN}) as c:
        yield c


def login(client, conn, discord_id: str = "1001", name: str = "Faker") -> int:
    """Create an allowed user with a live session and put the cookie on the client."""
    uid = users.upsert(conn, discord_id, name, None, T0)
    allowlist.add(conn, discord_id, T0)
    client.cookies.set("session", new_session(conn, uid, T0, 30))
    return uid
