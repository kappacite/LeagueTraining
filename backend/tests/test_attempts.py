import json

from conftest import login

P = "mid-drake-01"  # moyen (x2), time_limit 20, excellent = b, correct = c, erreur = a


def start(client, mode="normal", pid=P):
    return client.post(f"/api/puzzles/{pid}/start", json={"mode": mode})


def answer(client, choice, pid=P):
    return client.post(f"/api/puzzles/{pid}/answer", json={"choice": choice})


def test_requires_login(client):
    assert start(client).status_code == 401
    assert client.get("/api/puzzles").status_code == 401


def test_start_returns_public_view_only(client, conn):
    login(client, conn)
    r = start(client)
    assert r.status_code == 200
    body = json.dumps(r.json())
    assert "explanation" not in body and "lesson" not in body and "excellent" not in body
    assert r.json()["puzzle"]["id"] == P and r.json()["scored"] is True and r.json()["mode"] == "normal"


def test_answer_scores_with_multiplier(client, conn):
    login(client, conn)
    start(client)
    r = answer(client, "b").json()
    assert (r["grade"], r["points"], r["timed_out"], r["scored"]) == ("excellent", 6, False, True)
    assert r["lesson"] and {c["id"]: c["grade"] for c in r["choices"]} == {"a": "erreur", "b": "excellent", "c": "correct"}


def test_correct_on_facile_is_one_point(client, conn):
    login(client, conn)
    start(client, pid="adc-antiheal-01")
    assert answer(client, "a", pid="adc-antiheal-01").json()["points"] == 3


def test_second_answer_is_409(client, conn):
    login(client, conn)
    start(client)
    answer(client, "b")
    assert answer(client, "b").status_code == 409
    assert conn.execute("select sum(points) from attempts").fetchone()[0] == 6


def test_answer_without_start_is_409(client, conn):
    login(client, conn)
    assert answer(client, "b").status_code == 409


def test_restart_keeps_original_timer(client, conn, clock):
    login(client, conn)
    first = start(client, "chrono").json()
    clock.advance(seconds=10)
    again = start(client, "normal").json()
    assert again["mode"] == "chrono" and again["started_at"] == first["started_at"]
    assert conn.execute("select count(*) from attempts").fetchone()[0] == 1


def test_chrono_timeout(client, conn, clock):
    login(client, conn)
    start(client, "chrono")
    clock.advance(seconds=22.5)
    r = answer(client, "b").json()
    assert (r["grade"], r["timed_out"], r["points"]) == ("erreur", True, 0)


def test_chrono_within_grace(client, conn, clock):
    login(client, conn)
    start(client, "chrono")
    clock.advance(seconds=21.5)
    assert answer(client, "b").json()["grade"] == "excellent"


def test_normal_mode_has_no_timer(client, conn, clock):
    login(client, conn)
    start(client, "normal")
    clock.advance(minutes=10)
    assert answer(client, "b").json()["timed_out"] is False


def test_replay_gives_no_points(client, conn):
    login(client, conn)
    start(client)
    answer(client, "a")
    s = start(client).json()
    assert s["scored"] is False
    r = answer(client, "b").json()
    assert (r["grade"], r["points"], r["scored"]) == ("excellent", 0, False)
    assert conn.execute("select sum(points) from attempts").fetchone()[0] == 0


def test_unknown_choice_422(client, conn):
    login(client, conn)
    start(client)
    assert answer(client, "zz").status_code == 422
    assert answer(client, "b").status_code == 200  # attempt still open


def test_unknown_puzzle_404(client, conn):
    login(client, conn)
    assert start(client, pid="nope").status_code == 404
    assert answer(client, "a", pid="nope").status_code == 404


def test_bad_mode_422(client, conn):
    login(client, conn)
    assert start(client, mode="turbo").status_code == 422


def test_distribution_after_answer(client, conn):
    login(client, conn, "1", "Alice")
    start(client)
    answer(client, "a")
    login(client, conn, "2", "Bob")
    start(client)
    dist = answer(client, "b").json()["distribution"]
    assert [(d["name"], d["choice_id"]) for d in dist] == [("Alice", "a"), ("Bob", "b")]


def test_list_marks_done(client, conn):
    login(client, conn)
    start(client)
    answer(client, "c")
    rows = {p["id"]: p for p in client.get("/api/puzzles").json()}
    assert (rows[P]["done"], rows[P]["grade"]) == (True, "correct")
    assert (rows["adc-antiheal-01"]["done"], rows["adc-antiheal-01"]["grade"]) == (False, None)
    assert [p["id"] for p in client.get("/api/puzzles?role=adc").json()] == ["adc-antiheal-01"]
    assert "choices" not in rows[P]
