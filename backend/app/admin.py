"""Admin CLI: python -m app.admin {allow,revoke,list,sync-ddragon,backup}."""
import argparse
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .db import connect, migrate
from .ddragon import sync
from .repositories import allowlist


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.admin")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("allow", "revoke"):
        sub.add_parser(name).add_argument("discord_id")
    sub.add_parser("list")
    sub.add_parser("sync-ddragon")
    sub.add_parser("backup").add_argument("dest", type=Path)
    args = parser.parse_args(argv)

    data_dir = Path(os.environ.get("DATA_DIR", "/data"))
    if args.cmd == "sync-ddragon":
        with httpx.Client(timeout=30) as client:
            print("synced", sync(data_dir / "ddragon", client))
        return 0

    conn = connect(data_dir / "app.db")
    migrate(conn)
    try:
        if args.cmd == "allow":
            allowlist.add(conn, args.discord_id, datetime.now(UTC))
        elif args.cmd == "revoke":
            allowlist.remove(conn, args.discord_id)
        elif args.cmd == "list":
            print("\n".join(allowlist.all(conn)))
        elif args.cmd == "backup":
            args.dest.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(args.dest) as dest:
                conn.backup(dest)
            dest.close()
            print("backup written to", args.dest)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
