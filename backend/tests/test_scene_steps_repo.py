import sqlite3

import pytest

from app.repositories import attempts, scene_steps, users
from conftest import T0


def test_step_lifecycle(conn):
    uid = users.upsert(conn, "1", "a", None, T0)
    aid = attempts.create(conn, uid, "s", "normal", T0, True)
    sid = scene_steps.create(conn, aid, "n1", T0)
    assert scene_steps.current(conn, aid)["id"] == sid
    assert scene_steps.close(conn, sid, "b", "excellent", 6, False, T0) is True
    assert scene_steps.close(conn, sid, "a", "erreur", 0, False, T0) is False  # already answered
    assert scene_steps.current(conn, aid) is None
    scene_steps.create(conn, aid, "n2", T0)
    assert [(r["node_id"], r["choice_id"], r["points"]) for r in scene_steps.path(conn, aid)] == [("n1", "b", 6)]


def test_one_step_per_node(conn):
    uid = users.upsert(conn, "1", "a", None, T0)
    aid = attempts.create(conn, uid, "s", "normal", T0, True)
    scene_steps.create(conn, aid, "n1", T0)
    with pytest.raises(sqlite3.IntegrityError):
        scene_steps.create(conn, aid, "n1", T0)


def test_distribution_only_scored_attempts(conn):
    a = users.upsert(conn, "1", "Alice", None, T0)
    b = users.upsert(conn, "2", "Bob", None, T0)
    for uid, scored, choice in [(a, True, "b"), (b, False, "a")]:
        sid = scene_steps.create(conn, attempts.create(conn, uid, "s", "normal", T0, scored), "n1", T0)
        scene_steps.close(conn, sid, choice, "excellent", 0, False, T0)
    rows = scene_steps.distribution(conn, "s", "n1")
    assert [(r["name"], r["choice_id"]) for r in rows] == [("Alice", "b")]
