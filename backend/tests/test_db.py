import sqlite3

import pytest

from app.db import connect, migrate


def test_migrate_creates_tables_and_is_idempotent(tmp_path):
    conn = connect(tmp_path / "a.db")
    migrate(conn)
    migrate(conn)
    names = {r["name"] for r in conn.execute("select name from sqlite_master where type='table'")}
    assert {"users", "allowlist", "sessions", "attempts", "daily"} <= names
    assert conn.execute("pragma user_version").fetchone()[0] == 2


def test_only_one_scored_attempt_per_user_puzzle(conn):
    conn.execute("insert into users (discord_id, name, created_at) values ('1', 'a', 'now')")
    sql = ("insert into attempts (user_id, puzzle_id, mode, started_at, scored) "
           "values (1, 'p', 'normal', 'now', ?)")
    conn.execute(sql, (1,))
    conn.execute(sql, (0,))  # practice attempts are unlimited
    conn.execute(sql, (0,))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(sql, (1,))


def test_connection_can_be_closed_from_another_thread(tmp_path):
    # FastAPI may run a dependency's setup and teardown on different worker threads.
    import threading
    conn = connect(tmp_path / "a.db")
    errors = []

    def close():
        try:
            conn.close()
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    t = threading.Thread(target=close)
    t.start()
    t.join()
    assert errors == []
