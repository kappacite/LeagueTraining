from datetime import UTC, datetime, timedelta

from app.repositories import allowlist, attempts, daily, sessions, users

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)


def test_upsert_updates_name_and_avatar(conn):
    a = users.upsert(conn, "42", "old", None, NOW)
    b = users.upsert(conn, "42", "new", "abc", NOW)
    assert a == b
    row = users.get(conn, a)
    assert (row["name"], row["avatar"]) == ("new", "abc")
    assert users.get(conn, 999) is None
    assert [r["id"] for r in users.all(conn)] == [a]


def test_allowlist_add_list_idempotent(conn):
    allowlist.add(conn, "42", NOW)
    allowlist.add(conn, "42", NOW)
    assert allowlist.is_allowed(conn, "42") and not allowlist.is_allowed(conn, "7")
    assert allowlist.all(conn) == ["42"]


def test_revoke_deletes_sessions(conn):
    uid = users.upsert(conn, "42", "a", None, NOW)
    allowlist.add(conn, "42", NOW)
    sessions.create(conn, "h", uid, NOW + timedelta(days=1))
    allowlist.remove(conn, "42")
    assert sessions.user_id_for(conn, "h", NOW) is None
    assert not allowlist.is_allowed(conn, "42")


def test_session_lookup_and_delete(conn):
    uid = users.upsert(conn, "42", "a", None, NOW)
    sessions.create(conn, "h", uid, NOW + timedelta(days=1))
    assert sessions.user_id_for(conn, "h", NOW) == uid
    sessions.delete(conn, "h")
    assert sessions.user_id_for(conn, "h", NOW) is None


def test_expired_session_ignored(conn):
    uid = users.upsert(conn, "42", "a", None, NOW)
    sessions.create(conn, "h", uid, NOW - timedelta(seconds=1))
    assert sessions.user_id_for(conn, "h", NOW) is None


def test_attempt_lifecycle(conn):
    uid = users.upsert(conn, "42", "a", None, NOW)
    assert attempts.open_scored(conn, uid, "p") is None and not attempts.has_scored(conn, uid, "p")
    aid = attempts.create(conn, uid, "p", "chrono", NOW, scored=True)
    assert attempts.open_scored(conn, uid, "p")["id"] == aid
    assert attempts.has_scored(conn, uid, "p")
    attempts.close(conn, aid, "b", "excellent", 6, False, NOW, "2026-11-16")
    assert attempts.open_scored(conn, uid, "p") is None
    row = attempts.get(conn, aid)
    assert (row["choice_id"], row["grade"], row["points"], row["answered_day"]) == ("b", "excellent", 6, "2026-11-16")
    pid = attempts.create(conn, uid, "p", "normal", NOW, scored=False)
    assert attempts.open_practice(conn, uid, "p")["id"] == pid


def test_distribution_only_scored_answered(conn):
    a = users.upsert(conn, "1", "a", None, NOW)
    b = users.upsert(conn, "2", "b", None, NOW)
    c = users.upsert(conn, "3", "c", None, NOW)
    attempts.close(conn, attempts.create(conn, a, "p", "normal", NOW, True), "x", "erreur", 0, False, NOW, "d")
    attempts.close(conn, attempts.create(conn, b, "p", "normal", NOW, False), "y", "correct", 0, False, NOW, "d")
    attempts.create(conn, c, "p", "normal", NOW, True)  # open, not answered
    rows = attempts.distribution(conn, "p")
    assert [(r["name"], r["choice_id"]) for r in rows] == [("a", "x")]
    assert [r["name"] for r in attempts.done_by(conn, "p")] == ["a"]
    assert [(r["user_id"], r["points"]) for r in attempts.scored_answered(conn)] == [(a, 0)]
    assert attempts.scored_answered(conn, user_id=b) == []


def test_daily(conn):
    assert daily.get(conn, "2026-11-16") is None
    daily.set(conn, "2026-11-16", "p1")
    daily.set(conn, "2026-11-16", "p2")
    daily.set(conn, "2026-11-17", "p3")
    assert daily.get(conn, "2026-11-16") == "p2"
    assert daily.history(conn) == {"2026-11-16": "p2", "2026-11-17": "p3"}
