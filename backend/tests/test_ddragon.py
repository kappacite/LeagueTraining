import json

import httpx
import pytest

from app.ddragon import DDragonMissing, load, patches_behind, sync


def test_load_reads_fixture(dd):
    assert dd.version == "15.23.1"
    assert dd.champions["LeeSin"] == "Lee Sin"
    assert 3165 in dd.items
    assert "SummonerFlash" in dd.summoners


def test_load_missing_raises(tmp_path):
    with pytest.raises(DDragonMissing):
        load(tmp_path)


def test_patches_behind(dd):
    assert patches_behind("15.23.1", dd) == 0
    assert patches_behind("15.20.1", dd) == 3
    assert patches_behind("14.1.1", dd) == 4


def fake_cdn(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/api/versions.json":
        return httpx.Response(200, json=["9.1.1", "9.0.1"])
    if path.endswith("champion.json"):
        return httpx.Response(200, json={"data": {"Ahri": {"id": "Ahri", "name": "Ahri"}}})
    if path.endswith("item.json"):
        return httpx.Response(200, json={"data": {"3165": {"name": "Morello"}}})
    if path.endswith("summoner.json"):
        return httpx.Response(200, json={"data": {"SummonerFlash": {"id": "SummonerFlash", "name": "Flash"}}})
    if path.endswith(".png"):
        return httpx.Response(200, content=b"png")
    return httpx.Response(404)


def test_sync_writes_loadable_cache(tmp_path):
    client = httpx.Client(transport=httpx.MockTransport(fake_cdn))
    v = sync(tmp_path, client)
    dd = load(tmp_path)
    assert v == "9.1.1" == dd.version
    assert dd.champions == {"Ahri": "Ahri"}
    for img in ["champion/Ahri.png", "item/3165.png", "spell/SummonerFlash.png", "map/map11.png"]:
        assert (tmp_path / "img" / img).read_bytes() == b"png"


def test_sync_failure_leaves_no_loadable_partial_cache(tmp_path):
    def broken(request):
        if request.url.path.endswith(".png"):
            return httpx.Response(500)
        return fake_cdn(request)
    with pytest.raises(httpx.HTTPStatusError):
        sync(tmp_path, httpx.Client(transport=httpx.MockTransport(broken)))
    with pytest.raises(DDragonMissing):
        load(tmp_path)
