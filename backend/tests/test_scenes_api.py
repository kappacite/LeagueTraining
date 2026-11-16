import pytest
import yaml

from app.puzzles.loader import load_catalog
from conftest import FIXTURES, login

SCENES = FIXTURES / "scenes"
S = "scene-drake"  # moyen (x2). n1: a erreur→dead, b excellent→n2, c correct→n2. n2: a erreur→lost, b excellent→best
FORBIDDEN = {"grade", "explanation", "consequence", "next", "ending", "endings", "nodes", "lesson", "end"}


@pytest.fixture
def catalog_dir():
    return SCENES


def keys(obj) -> set[str]:
    if isinstance(obj, dict):
        return set(obj) | {k for v in obj.values() for k in keys(v)}
    if isinstance(obj, list):
        return {k for v in obj for k in keys(v)}
    return set()


def start(client, mode="normal"):
    return client.post(f"/api/puzzles/{S}/start", json={"mode": mode})


def answer(client, choice):
    return client.post(f"/api/puzzles/{S}/answer", json={"choice": choice})


def test_start_returns_first_node_only(client, conn):
    login(client, conn)
    r = start(client).json()
    assert r["step"]["id"] == "n1" and r["scored"] is True
    assert [c["id"] for c in r["step"]["choices"]] == ["a", "b", "c"]
    assert "n2" not in str(r) and not keys(r) & FORBIDDEN


def test_excellent_path_reaches_best_end(client, conn):
    login(client, conn)
    start(client)
    first = answer(client, "b").json()
    assert first["grade"] == "excellent" and first["points"] == 6 and first["next"]["id"] == "n2"
    assert "end" not in first and first["consequence"]
    last = answer(client, "b").json()
    assert last["end"]["reached"]["id"] == "best" and last["end"]["total_points"] == 12
    assert last["end"]["optimal"]["id"] == "best"
    row = conn.execute("select grade, points, choice_id from attempts").fetchone()
    assert tuple(row) == ("excellent", 12, "best")


def test_erreur_ends_immediately(client, conn):
    login(client, conn)
    start(client)
    r = answer(client, "a").json()
    assert "next" not in r
    assert r["end"]["reached"]["id"] == "dead" and r["end"]["optimal"]["id"] == "best"
    assert r["end"]["reached"]["outcome"]["drakes"] == -1
    assert r["end"]["path"] == [{"node_id": "n1", "choice_id": "a", "grade": "erreur", "points": 0}]
    assert r["end"]["optimal_path"] == [{"node_id": "n1", "choice_id": "b"}, {"node_id": "n2", "choice_id": "b"}]


def test_end_payload_has_both_replays(client, conn):
    login(client, conn)
    start(client)
    end = answer(client, "a").json()["end"]
    assert len(end["replay"]["mine"]) == 2 and len(end["replay"]["optimal"]) == 4
    assert end["lesson"]


def test_worst_grade_kept_on_attempt(client, conn):
    login(client, conn)
    start(client)
    answer(client, "c")
    answer(client, "b")
    assert tuple(conn.execute("select grade, points from attempts").fetchone()) == ("correct", 2 + 6)


def test_restart_resumes_current_node(client, conn, clock):
    login(client, conn)
    start(client, "chrono")
    clock.advance(seconds=5)
    answer(client, "b")
    clock.advance(seconds=3)
    again = start(client, "normal").json()
    assert again["step"]["id"] == "n2" and again["mode"] == "chrono"
    assert again["step"]["started_at"].startswith("2026-11-16T12:00:05")


def test_answer_after_end_409(client, conn):
    login(client, conn)
    start(client)
    answer(client, "a")
    assert answer(client, "b").status_code == 409
    assert conn.execute("select sum(points) from scene_steps").fetchone()[0] == 0


def test_answer_without_start_409(client, conn):
    login(client, conn)
    assert answer(client, "a").status_code == 409


def test_unknown_choice_422(client, conn):
    login(client, conn)
    start(client)
    assert answer(client, "zz").status_code == 422
    assert answer(client, "b").status_code == 200


def test_chrono_counts_from_end_of_intro(client, conn, clock):
    # n1 intro lasts 4 s: the 15 s answer window (+2 s grace) starts once the choices are shown.
    login(client, conn)
    start(client, "chrono")
    clock.advance(seconds=20.5)
    assert answer(client, "b").json()["timed_out"] is False


def test_next_node_window_includes_previous_consequence(client, conn, clock):
    # n1.b consequence lasts 3 s and n2 intro 0 s: n2 allows 3 + 15 + 2 = 20 s after n1 was answered.
    login(client, conn)
    start(client, "chrono")
    answer(client, "b")
    clock.advance(seconds=20.5)
    assert answer(client, "b").json()["timed_out"] is True


def test_timeout_still_follows_choice(client, conn, clock):
    login(client, conn)
    start(client, "chrono")
    clock.advance(seconds=21.5)  # n1: intro 4 + time_limit 15 + 2 s grace
    r = answer(client, "c").json()
    assert (r["grade"], r["timed_out"], r["points"]) == ("erreur", True, 0)
    assert r["next"]["id"] == "n2"


def test_chrono_is_per_node(client, conn, clock):
    login(client, conn)
    start(client, "chrono")
    clock.advance(seconds=10)
    answer(client, "b")
    clock.advance(seconds=10)  # 20 s since scene start, 10 s on n2
    assert answer(client, "b").json()["timed_out"] is False


def test_current_node_removed_from_yaml(client, conn, app, dd, tmp_path):
    login(client, conn)
    start(client)
    answer(client, "b")  # now on n2
    data = yaml.safe_load((SCENES / "scene-drake.yaml").read_text(encoding="utf-8"))
    data["nodes"]["m2"] = data["nodes"].pop("n2")
    for c in data["nodes"]["n1"]["choices"]:
        if c.get("next") == "n2":
            c["next"] = "m2"
    edited = tmp_path / "edited"
    edited.mkdir()
    (edited / "s.yaml").write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    app.state.catalog = load_catalog(edited, dd)
    r = start(client)
    assert r.status_code == 200
    assert (r.json()["step"]["id"], r.json()["scored"]) == ("n1", False)


def test_no_future_leaks(client, conn):
    login(client, conn)
    s = start(client).json()
    nxt = answer(client, "b").json()["next"]
    assert not keys(s) & FORBIDDEN and not keys(nxt) & FORBIDDEN


def test_practice_replay_is_unscored(client, conn):
    login(client, conn)
    start(client)
    answer(client, "a")
    s = start(client).json()
    assert (s["scored"], s["step"]["id"]) == (False, "n1")
    r = answer(client, "b").json()
    assert (r["points"], r["scored"]) == (0, False)


def test_scene_counts_in_leaderboard_and_profile(client, conn):
    uid = login(client, conn)
    start(client)
    answer(client, "b")
    answer(client, "b")
    general = client.get("/api/leaderboard").json()["general"]
    assert general[0]["points"] == 12
    assert client.get(f"/api/users/{uid}").json()["by_role"]["mid"] == {"answered": 1, "excellent": 1, "points": 12}
    listed = client.get("/api/puzzles").json()
    assert (listed[0]["done"], listed[0]["grade"]) == (True, "excellent")


def test_distribution_per_node(client, conn):
    login(client, conn, "1", "Alice")
    start(client)
    answer(client, "c")
    login(client, conn, "2", "Bob")
    start(client)
    dist = answer(client, "b").json()["distribution"]
    assert [(d["name"], d["choice_id"]) for d in dist] == [("Alice", "c"), ("Bob", "b")]
