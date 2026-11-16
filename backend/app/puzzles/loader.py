from pathlib import Path

import yaml
from pydantic import TypeAdapter, ValidationError

from ..ddragon import DDragon, patches_behind
from . import Puzzle

STALE_AFTER = 2  # patches
_adapter = TypeAdapter(Puzzle)


class PuzzleLoadError(Exception):
    pass


class Catalog:
    def __init__(self, puzzles: list, dd: DDragon):
        self._by_id = {p.id: p for p in puzzles}
        self._dd = dd

    def get(self, puzzle_id: str):
        return self._by_id.get(puzzle_id)

    def all(self) -> list:
        return list(self._by_id.values())

    def ids(self) -> set[str]:
        return set(self._by_id)

    def filter(self, role=None, difficulty=None, type=None) -> list:
        return [p for p in self._by_id.values()
                if (role is None or p.role == role)
                and (difficulty is None or p.difficulty == difficulty)
                and (type is None or p.type == type)]

    def is_stale(self, p) -> bool:
        return p.type == "itemization" and patches_behind(p.patch, self._dd) > STALE_AFTER


def _ref_errors(p, dd: DDragon) -> list[str]:
    errors = [f"unknown champion '{c}'" for c in sorted(p.champion_refs() - dd.champions.keys())]
    errors += [f"unknown item {i}" for i in sorted(p.item_refs() - dd.items.keys())]
    errors += [f"unknown summoner '{s}'" for s in sorted(p.summoner_refs() - dd.summoners.keys())]
    return errors


def load_catalog(puzzles_dir: Path, dd: DDragon) -> Catalog:
    """Load every *.yaml under puzzles_dir. Collects all errors and raises them together."""
    puzzles, errors, seen = [], [], {}
    for f in sorted(puzzles_dir.rglob("*.yaml")):
        rel = f.relative_to(puzzles_dir).as_posix()
        try:
            p = _adapter.validate_python(yaml.safe_load(f.read_text(encoding="utf-8")))
        except (ValidationError, yaml.YAMLError) as e:
            errors.append(f"{rel}: {e}")
            continue
        errs = _ref_errors(p, dd)
        if p.id in seen:
            errs.append(f"duplicate id '{p.id}' (also in {seen[p.id]})")
        seen.setdefault(p.id, rel)
        errors += [f"{rel}: {e}" for e in errs]
        if not errs:
            puzzles.append(p)
    if not errors and not puzzles:
        errors.append(f"no puzzle found in {puzzles_dir} (check PUZZLES_DIR)")
    if errors:
        raise PuzzleLoadError("\n".join(errors))
    return Catalog(puzzles, dd)
