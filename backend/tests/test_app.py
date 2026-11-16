import shutil

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.puzzles.loader import PuzzleLoadError
from conftest import FIXTURES, ORIGIN


def no_network(*a, **kw):
    raise httpx.ConnectError("offline")


@pytest.fixture
def offline(monkeypatch):
    # Patch only the startup sync: TestClient itself is an httpx.Client.
    monkeypatch.setattr(main, "sync", no_network)


def test_startup_uses_cache_without_network(settings, offline):
    shutil.copytree(FIXTURES / "ddragon", settings.ddragon_dir)
    with TestClient(main.create_app(settings), base_url=ORIGIN) as c:
        assert c.get("/api/meta").json() == {"ddragon_version": "15.23.1"}


def test_startup_fails_clearly_without_cache_and_network(settings, offline):
    with pytest.raises(RuntimeError, match="sync-ddragon"):
        main.create_app(settings)


def test_startup_syncs_when_cache_missing(settings, monkeypatch):
    def fake_sync(cache_dir, client):
        shutil.copytree(FIXTURES / "ddragon", cache_dir, dirs_exist_ok=True)
        return "15.23.1"
    monkeypatch.setattr(main, "sync", fake_sync)
    assert main.create_app(settings).state.dd.version == "15.23.1"


def test_invalid_puzzle_blocks_startup(settings, dd, tmp_path):
    bad = tmp_path / "bad_puzzles"
    bad.mkdir()
    (bad / "x.yaml").write_text("id: x\ntype: decision\n", encoding="utf-8")
    settings.puzzles_dir = bad
    with pytest.raises(PuzzleLoadError):
        main.create_app(settings, dd=dd)


def test_static_index_served(settings, dd):
    settings.static_dir.mkdir()
    (settings.static_dir / "index.html").write_text("<h1>LeagueTraining</h1>", encoding="utf-8")
    (settings.static_dir / "assets").mkdir()
    (settings.static_dir / "assets" / "app-abc123.js").write_text("1", encoding="utf-8")
    with TestClient(main.create_app(settings, dd=dd), base_url=ORIGIN) as c:
        r = c.get("/")
        assert "LeagueTraining" in r.text and "content-security-policy" in r.headers
        assert r.headers["cache-control"] == "no-cache"  # new deploys must reach browsers
        assert c.get("/assets/app-abc123.js").headers["cache-control"] == "public, max-age=31536000, immutable"
        assert c.get("/api/me").status_code == 401  # API not shadowed by the static mount


def test_ddragon_images_served(settings, dd):
    img = settings.ddragon_dir / "img" / "champion"
    img.mkdir(parents=True)
    (img / "Ahri.png").write_bytes(b"png")
    with TestClient(main.create_app(settings, dd=dd), base_url=ORIGIN) as c:
        assert c.get("/dd/champion/Ahri.png").content == b"png"
