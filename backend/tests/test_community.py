import random
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.puzzles.loader import load_catalog
from app.repositories import attempts, daily as daily_repo, users
from app.services import daily, stats
from conftest import FIXTURES, T0, login

PARIS = ZoneInfo("Europe/Paris")


@pytest.fixture
def catalog(dd):
    return load_catalog(FIXTURES / "puzzles", dd)


def scored(conn, uid, pid, grade, points, day):
    attempts.close(conn, attempts.create(conn, uid, pid, "normal", T0, True), "a", grade, points, False, T0, day)


def test_daily_stable_within_day(conn, catalog):
    a = daily.today(conn, catalog, T0, PARIS, random.Random(1))
    b = daily.today(conn, catalog, T0 + timedelta(hours=5), PARIS, random.Random(2))
    assert a.id == b.id


def test_daily_changes_at_paris_midnight(conn, catalog):
    daily.today(conn, catalog, datetime(2026, 11, 16, 22, 59, tzinfo=UTC), PARIS, random.Random(1))
    daily.today(conn, catalog, datetime(2026, 11, 16, 23, 1, tzinfo=UTC), PARIS, random.Random(1))
    assert list(daily_repo.history(conn)) == ["2026-11-16", "2026-11-17"]


def test_daily_no_repeat_until_exhausted(conn, catalog):
    days = [daily.today(conn, catalog, T0 + timedelta(days=i), PARIS, random.Random(i)).id for i in range(3)]
    assert days[0] != days[1]
    assert days[2] == days[0]  # oldest last appearance comes back first


def test_daily_reassigned_when_puzzle_removed(conn, catalog):
    daily_repo.set(conn, "2026-11-16", "deleted-puzzle")
    p = daily.today(conn, catalog, T0, PARIS, random.Random(1))
    assert p.id in catalog.ids()
    assert daily_repo.get(conn, "2026-11-16") == p.id


def test_leaderboard_ignores_unknown_puzzles(conn, catalog):
    a = users.upsert(conn, "1", "Alice", None, T0)
    b = users.upsert(conn, "2", "Bob", None, T0)
    scored(conn, a, "mid-drake-01", "excellent", 6, "2026-11-16")
    scored(conn, b, "deleted-puzzle", "excellent", 9, "2026-11-16")
    general = stats.leaderboard(conn, catalog, {})["general"]
    assert [(r["name"], r["points"], r["answered"]) for r in general] == [("Alice", 6, 1), ("Bob", 0, 0)]


def test_leaderboard_daily_counts_only_same_day(conn, catalog):
    a = users.upsert(conn, "1", "Alice", None, T0)
    scored(conn, a, "mid-drake-01", "excellent", 6, "2026-11-16")      # daily, same day
    scored(conn, a, "adc-antiheal-01", "excellent", 3, "2026-11-16")   # not the daily
    history = {"2026-11-16": "mid-drake-01", "2026-11-17": "adc-antiheal-01"}
    assert stats.leaderboard(conn, catalog, history)["daily"][0]["points"] == 6


def test_profile_by_role(conn, catalog):
    a = users.upsert(conn, "1", "Alice", None, T0)
    scored(conn, a, "mid-drake-01", "excellent", 6, "d")
    scored(conn, a, "adc-antiheal-01", "erreur", 0, "d")
    p = stats.profile(conn, catalog, a)
    assert p["total_points"] == 6
    assert p["by_role"]["mid"] == {"answered": 1, "excellent": 1, "points": 6}
    assert p["by_role"]["adc"] == {"answered": 1, "excellent": 0, "points": 0}
    assert p["by_role"]["top"] == {"answered": 0, "excellent": 0, "points": 0}
    assert p["by_difficulty"]["moyen"]["points"] == 6


def test_daily_route_shows_who_did_it(client, conn):
    login(client, conn, "1", "Alice")
    d = client.get("/api/daily").json()
    pid = d["puzzle"]["id"]
    assert d["done_by"] == [] and "choices" not in d["puzzle"]
    client.post(f"/api/puzzles/{pid}/start", json={"mode": "normal"})
    client.post(f"/api/puzzles/{pid}/answer", json={"choice": "a"})
    assert [u["name"] for u in client.get("/api/daily").json()["done_by"]] == ["Alice"]


def test_leaderboard_and_profile_routes(client, conn):
    uid = login(client, conn)
    lb = client.get("/api/leaderboard").json()
    assert set(lb) == {"general", "daily"}
    assert client.get(f"/api/users/{uid}").json()["user"]["name"] == "Faker"


def test_unknown_user_404(client, conn):
    login(client, conn)
    assert client.get("/api/users/999").status_code == 404
