import sqlite3
from pathlib import Path

MIGRATIONS = Path(__file__).parent / "migrations"


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    # One connection per request, never shared concurrently; FastAPI may close it on another thread.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma journal_mode=wal")
    conn.execute("pragma foreign_keys=on")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    """Apply migrations/NNN_*.sql newer than PRAGMA user_version, in order."""
    current = conn.execute("pragma user_version").fetchone()[0]
    for f in sorted(MIGRATIONS.glob("*.sql")):
        n = int(f.name.split("_", 1)[0])
        if n > current:
            conn.executescript(f.read_text(encoding="utf-8"))
            conn.execute(f"pragma user_version = {n}")
    conn.commit()
