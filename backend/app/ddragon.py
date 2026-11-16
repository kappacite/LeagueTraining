"""Local cache of Riot's Data Dragon (champions, items, summoner spells, images)."""
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import httpx

BASE = "https://ddragon.leagueoflegends.com"
LANG = "fr_FR"
DATA_FILES = ("champion", "item", "summoner")


class DDragonMissing(Exception):
    pass


@dataclass(frozen=True)
class DDragon:
    version: str
    versions: list[str]
    champions: dict[str, str]  # id -> display name
    items: dict[int, str]
    summoners: dict[str, str]


def load(cache_dir: Path) -> DDragon:
    try:
        versions = json.loads((cache_dir / "versions.json").read_text(encoding="utf-8"))
        data = {n: json.loads((cache_dir / f"{n}.json").read_text(encoding="utf-8"))["data"] for n in DATA_FILES}
    except FileNotFoundError as e:
        raise DDragonMissing(str(e)) from e
    return DDragon(
        version=versions[0],
        versions=versions,
        champions={k: v["name"] for k, v in data["champion"].items()},
        items={int(k): v["name"] for k, v in data["item"].items()},
        summoners={k: v["name"] for k, v in data["summoner"].items()},
    )


def sync(cache_dir: Path, client: httpx.Client) -> str:
    """Download the latest version. JSON indexes are written last, so a failed sync never looks complete."""
    def get(url: str) -> httpx.Response:
        r = client.get(url)
        r.raise_for_status()
        return r

    versions = get(f"{BASE}/api/versions.json").json()
    v = versions[0]
    data = {n: get(f"{BASE}/cdn/{v}/data/{LANG}/{n}.json").json() for n in DATA_FILES}
    images = ([f"champion/{k}.png" for k in data["champion"]["data"]]
              + [f"item/{k}.png" for k in data["item"]["data"]]
              + [f"spell/{k}.png" for k in data["summoner"]["data"]]
              + ["map/map11.png"])

    def fetch(rel: str) -> None:
        dest = cache_dir / "img" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(get(f"{BASE}/cdn/{v}/img/{rel}").content)

    for f in ["versions.json", *(f"{n}.json" for n in DATA_FILES)]:
        (cache_dir / f).unlink(missing_ok=True)
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(fetch, images))
    for n, d in data.items():
        (cache_dir / f"{n}.json").write_text(json.dumps(d), encoding="utf-8")
    (cache_dir / "versions.json").write_text(json.dumps(versions), encoding="utf-8")
    return v


def patches_behind(patch: str, dd: DDragon) -> int:
    return dd.versions.index(patch) if patch in dd.versions else len(dd.versions)
