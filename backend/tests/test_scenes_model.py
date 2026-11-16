import json
from pathlib import Path

import pytest
import yaml

from app.puzzles.loader import PuzzleLoadError, load_catalog
from conftest import FIXTURES

SCENES = FIXTURES / "scenes"
SCENE = SCENES / "scene-drake.yaml"
FORBIDDEN = {"grade", "explanation", "consequence", "next", "ending", "endings", "nodes", "lesson"}


def scene(dd):
    return load_catalog(SCENES, dd).get("scene-drake")


def keys(obj) -> set[str]:
    if isinstance(obj, dict):
        return set(obj) | {k for v in obj.values() for k in keys(v)}
    if isinstance(obj, list):
        return {k for v in obj for k in keys(v)}
    return set()


def write(tmp_path: Path, data: dict) -> None:
    (tmp_path / "s.yaml").write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def base_data() -> dict:
    return yaml.safe_load(SCENE.read_text(encoding="utf-8"))


def test_fixture_scene_loads(dd):
    p = scene(dd)
    assert p.type == "scene" and p.start == "n1" and set(p.nodes) == {"n1", "n2"}


def test_optimal_path(dd):
    assert scene(dd).optimal_path() == [("n1", "b"), ("n2", "b")]


def test_ending_of_path(dd):
    p = scene(dd)
    assert p.ending_of([("n1", "a")]) == "dead"
    assert p.ending_of([("n1", "c"), ("n2", "b")]) == "best"


def test_clips_for_path_order(dd):
    p = scene(dd)
    clips = p.clips_for([("n1", "b"), ("n2", "b")])
    assert len(clips) == 4
    assert clips[0] == p.nodes["n1"].intro and clips[1] == p.nodes["n1"].choices[1].consequence
    assert clips[2] == p.nodes["n2"].intro


def test_public_views_hide_future(dd):
    p = scene(dd)
    start = p.public(stale=False).model_dump()
    node = p.public_node("n1").model_dump()
    assert not keys(start) & FORBIDDEN, keys(start) & FORBIDDEN
    assert not keys(node) & FORBIDDEN, keys(node) & FORBIDDEN
    assert [c["id"] for c in node["choices"]] == ["a", "b", "c"]
    assert node["intro"][1]["champions"][0]["hidden"] is True


def test_scene_champion_refs_checked(tmp_path, dd):
    d = base_data()
    d["nodes"]["n2"]["intro"][0]["champions"][0]["champion"] = "Teemoo"
    write(tmp_path, d)
    with pytest.raises(PuzzleLoadError, match="Teemoo"):
        load_catalog(tmp_path, dd)


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d["nodes"]["n1"]["choices"][0].update(ending=None, next="n2"), "must end the scene"),
    (lambda d: d["nodes"]["n1"]["choices"][1].update(ending="best"), "exactly one of next / ending"),
    (lambda d: d["nodes"]["n2"]["choices"][1].update(next="n1", ending=None), "cycle"),
    (lambda d: d["nodes"]["n1"]["choices"][2].update(grade="excellent"), "exactly one 'excellent'"),
    (lambda d: d.update(start="zz"), "is not a node"),
    (lambda d: d["nodes"]["n1"]["choices"][1].update(next="zz"), "is not a node"),
    (lambda d: d["nodes"]["n2"]["choices"][1].update(ending="zz"), "is not an ending"),
    (lambda d: d["endings"].update(orphan={"title": "x", "outcome": {}}), "ending 'orphan' is unreachable"),
    (lambda d: d["nodes"].update(n9=d["nodes"]["n2"]), "node 'n9' is unreachable"),
    (lambda d: d["nodes"]["n1"]["intro"][1].update(t=0), "increasing"),
    (lambda d: d["nodes"]["n1"]["intro"][0]["champions"][0].update(me=False), "exactly one 'me'"),
])
def test_graph_errors(tmp_path, dd, mutate, message):
    d = base_data()
    mutate(d)
    write(tmp_path, d)
    with pytest.raises(PuzzleLoadError, match=message.replace("(", r"\(")):
        load_catalog(tmp_path, dd)


def test_more_than_three_decisions_rejected(tmp_path, dd):
    d = base_data()
    n2 = d["nodes"]["n2"]
    for name, nxt in [("n2", "n3"), ("n3", "n4"), ("n4", None)]:
        node = json.loads(json.dumps(n2))
        if nxt:
            node["choices"][1].update(next=nxt, ending=None)
        d["nodes"][name] = node
    write(tmp_path, d)
    with pytest.raises(PuzzleLoadError, match="more than 3 decisions"):
        load_catalog(tmp_path, dd)
