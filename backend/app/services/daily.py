import random
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from ..puzzles.loader import Catalog
from ..repositories import daily as repo


def today(conn: sqlite3.Connection, catalog: Catalog, now: datetime, tz: ZoneInfo, rng: random.Random):
    """Today's puzzle (local date in tz). Picked once, then frozen; never repeats until all have been used."""
    date = now.astimezone(tz).date().isoformat()
    current = repo.get(conn, date)
    if current in catalog.ids():
        return catalog.get(current)
    history = {d: pid for d, pid in repo.history(conn).items() if d != date}
    fresh = sorted(catalog.ids() - set(history.values()))
    if fresh:
        pick = rng.choice(fresh)
    else:
        last_seen = {}
        for d, pid in sorted(history.items()):
            last_seen[pid] = d
        pick = min((pid for pid in catalog.ids()), key=lambda pid: (last_seen.get(pid, ""), pid))
    repo.set(conn, date, pick)
    return catalog.get(pick)
