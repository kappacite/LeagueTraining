import json
import os
import shutil
from pathlib import Path

import pytest
import yaml

from app.ddragon import DDragonMissing, load
from app.puzzles.loader import PuzzleLoadError, load_catalog

FIXTURES = Path(__file__).parent / "fixtures" / "puzzles"
REPO_PUZZLES = Path(__file__).parents[2] / "puzzles"


def write(dir: Path, name: str, data: dict) -> None:
    (dir / name).write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def fixture_data(rel: str) -> dict:
    return yaml.safe_load((FIXTURES / rel).read_text(encoding="utf-8"))


def test_loads_fixture_puzzles(dd):
    cat = load_catalog(FIXTURES, dd)
    assert sorted(p.id for p in cat.all()) == ["adc-antiheal-01", "mid-drake-01"]
    assert cat.get("mid-drake-01").type == "decision"
    assert cat.get("nope") is None


def test_public_view_has_no_answers(dd):
    for p in load_catalog(FIXTURES, dd).all():
        dumped = json.dumps(p.public(stale=False).model_dump())
        for secret in ("grade", "explanation", "lesson", "excellent", "Prio + vision"):
            assert secret not in dumped, (p.id, secret)


def test_public_view_keeps_scene_and_choice_items(dd):
    cat = load_catalog(FIXTURES, dd)
    pub = cat.get("mid-drake-01").public(stale=False).model_dump()
    assert pub["scene"]["champions"][1]["last_seen"] == 10
    assert [c["id"] for c in pub["choices"]] == ["a", "b", "c"]
    assert cat.get("adc-antiheal-01").public(stale=True).model_dump()["choices"][0]["items"] == [3033]


def test_grade_returns_choice(dd):
    p = load_catalog(FIXTURES, dd).get("mid-drake-01")
    assert p.grade("b").grade == "excellent"
    assert p.grade("zz") is None


def test_filter(dd):
    cat = load_catalog(FIXTURES, dd)
    assert [p.id for p in cat.filter(role="adc")] == ["adc-antiheal-01"]
    assert [p.id for p in cat.filter(type="decision", difficulty="moyen")] == ["mid-drake-01"]
    assert cat.filter(role="top") == []


def test_errors_collected(tmp_path, dd):
    bad_champ = fixture_data("mid/drake.yaml")
    bad_champ["id"] = "x1"
    bad_champ["scene"]["champions"][1]["champion"] = "Teemoo"
    no_excellent = fixture_data("adc/antiheal.yaml")
    no_excellent["choices"][0]["grade"] = "correct"
    write(tmp_path, "a.yaml", bad_champ)
    write(tmp_path, "b.yaml", no_excellent)
    with pytest.raises(PuzzleLoadError) as e:
        load_catalog(tmp_path, dd)
    msg = str(e.value)
    assert "a.yaml" in msg and "Teemoo" in msg
    assert "b.yaml" in msg and "excellent" in msg


def test_unknown_item_rejected(tmp_path, dd):
    data = fixture_data("adc/antiheal.yaml")
    data["choices"][0]["items"] = [99999]
    write(tmp_path, "a.yaml", data)
    with pytest.raises(PuzzleLoadError, match="99999"):
        load_catalog(tmp_path, dd)


def test_duplicate_ids_rejected(tmp_path, dd):
    shutil.copy(FIXTURES / "mid/drake.yaml", tmp_path / "a.yaml")
    shutil.copy(FIXTURES / "mid/drake.yaml", tmp_path / "b.yaml")
    with pytest.raises(PuzzleLoadError, match="mid-drake-01"):
        load_catalog(tmp_path, dd)


def test_unknown_field_rejected(tmp_path, dd):
    data = fixture_data("mid/drake.yaml")
    data["difficulte"] = "moyen"
    write(tmp_path, "a.yaml", data)
    with pytest.raises(PuzzleLoadError, match="difficulte"):
        load_catalog(tmp_path, dd)


def test_decision_requires_exactly_one_me(tmp_path, dd):
    data = fixture_data("mid/drake.yaml")
    data["scene"]["champions"][1]["me"] = True
    write(tmp_path, "a.yaml", data)
    with pytest.raises(PuzzleLoadError, match="me"):
        load_catalog(tmp_path, dd)


def test_stale_only_for_itemization(tmp_path, dd):
    for rel in ("mid/drake.yaml", "adc/antiheal.yaml"):
        data = fixture_data(rel)
        data["patch"] = "15.20.1"
        write(tmp_path, rel.replace("/", "-"), data)
    cat = load_catalog(tmp_path, dd)
    assert cat.is_stale(cat.get("adc-antiheal-01")) is True
    assert cat.is_stale(cat.get("mid-drake-01")) is False
    assert cat.is_stale(load_catalog(FIXTURES, dd).get("adc-antiheal-01")) is False


def test_repo_puzzles_are_valid():
    cache = Path(os.environ.get("DDRAGON_DIR", Path(__file__).parents[2] / "data" / "ddragon"))
    try:
        real = load(cache)
    except DDragonMissing:
        pytest.skip("no real Data Dragon cache; run python -m app.admin sync-ddragon")
    assert load_catalog(REPO_PUZZLES, real).all()


def test_missing_or_empty_dir_rejected(tmp_path, dd):
    with pytest.raises(PuzzleLoadError, match="no puzzle"):
        load_catalog(tmp_path / "nope", dd)
    with pytest.raises(PuzzleLoadError, match="no puzzle"):
        load_catalog(tmp_path, dd)
