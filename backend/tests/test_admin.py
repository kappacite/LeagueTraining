import sqlite3

from app import admin


def test_admin_allow_list_revoke(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert admin.main(["allow", "42"]) == 0
    assert admin.main(["list"]) == 0
    assert "42" in capsys.readouterr().out
    assert admin.main(["revoke", "42"]) == 0
    admin.main(["list"])
    assert "42" not in capsys.readouterr().out


def test_admin_backup_creates_readable_copy(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    admin.main(["allow", "42"])
    dest = tmp_path / "backup" / "b.db"
    assert admin.main(["backup", str(dest)]) == 0
    assert sqlite3.connect(dest).execute("select discord_id from allowlist").fetchall() == [("42",)]
