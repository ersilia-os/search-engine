"""Tests for normalization, catalog building, and the fetch/cache logic."""

import json

import pytest

import ersilia_search.io.loader as loader
from ersilia_search.io.loader import build_catalog, normalize


# --- normalize -------------------------------------------------------------


def test_normalize_wraps_scalar_multi():
    assert normalize({"Tag": "Solubility"})["Tag"] == ["Solubility"]


def test_normalize_none_multi_becomes_list():
    assert normalize({"Tag": None})["Tag"] == []


def test_normalize_none_text_becomes_empty_string():
    assert normalize({"Title": None})["Title"] == ""


def test_normalize_passes_unknown_fields_through():
    assert normalize({"Image Size": 1427.77})["Image Size"] == 1427.77


# --- build_catalog ---------------------------------------------------------


def test_facets_flatten_multi_and_skip_empties():
    cat = build_catalog(
        [
            {"Tag": ["A", "B"], "Task": "Annotation"},
            {"Tag": ["B", ""], "Task": ""},
        ]
    )
    assert cat.facets["Tag"] == ["A", "B"]  # flattened, deduped, empty dropped
    assert cat.facets["Task"] == ["Annotation"]  # empty Task skipped


def test_tokens_precomputed():
    cat = build_catalog([{"Title": "Natural Product"}])
    assert cat.text_tokens[0]["Title"] == ["natural", "product"]


# --- fetch + cache ---------------------------------------------------------


class FakeResp:
    def __init__(self, status=200, data=None, etag='"v1"'):
        self.status_code = status
        self._data = data
        self.headers = {"ETag": etag}

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


SAMPLE = [{"Identifier": "eos1", "Title": "Alpha"}]


@pytest.fixture
def clean_cache(monkeypatch):
    """Reset the module-level cache and clear data env vars around each test."""
    for var in (
        "ERSILIA_SEARCH_DATA",
        "ERSILIA_SEARCH_DATA_URL",
        "ERSILIA_SEARCH_CACHE_TTL",
    ):
        monkeypatch.delenv(var, raising=False)
    loader._cache, loader._fetched_at, loader._etag = None, 0.0, None
    yield
    loader._cache, loader._fetched_at, loader._etag = None, 0.0, None


def test_cache_reused_within_ttl(clean_cache, monkeypatch):
    calls = {"n": 0}

    def fake_get(url, headers=None, timeout=None):
        calls["n"] += 1
        return FakeResp(data=SAMPLE)

    monkeypatch.setattr(loader.httpx, "get", fake_get)
    c1 = loader.get_catalog(url="http://x")
    c2 = loader.get_catalog(url="http://x")
    assert calls["n"] == 1  # second call served from memory, no refetch
    assert c1 is c2


def test_not_modified_keeps_cache(clean_cache, monkeypatch):
    responses = [FakeResp(data=SAMPLE, etag='"v1"'), FakeResp(status=304, etag='"v1"')]
    monkeypatch.setattr(loader.httpx, "get", lambda *a, **k: responses.pop(0))
    c1 = loader.get_catalog(url="http://x")
    loader._fetched_at = 0.0  # force the TTL to be considered expired
    c2 = loader.get_catalog(url="http://x")
    assert c1 is c2  # 304 -> the cached catalog is kept


def test_serves_stale_on_fetch_failure(clean_cache, monkeypatch):
    state = {"first": True}

    def fake_get(url, headers=None, timeout=None):
        if state["first"]:
            state["first"] = False
            return FakeResp(data=SAMPLE)
        raise RuntimeError("network down")

    monkeypatch.setattr(loader.httpx, "get", fake_get)
    c1 = loader.get_catalog(url="http://x")
    loader._fetched_at = 0.0
    c2 = loader.get_catalog(url="http://x")  # refetch fails -> stale served, no raise
    assert c2 is c1


def test_raises_when_no_cache_and_fetch_fails(clean_cache, monkeypatch):
    def fake_get(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(loader.httpx, "get", fake_get)
    with pytest.raises(RuntimeError):
        loader.get_catalog(url="http://x")


def test_path_override_bypasses_network(clean_cache, monkeypatch, tmp_path):
    f = tmp_path / "m.json"
    f.write_text(json.dumps(SAMPLE))

    def boom(*a, **k):
        raise AssertionError("must not hit the network when a path is given")

    monkeypatch.setattr(loader.httpx, "get", boom)
    cat = loader.get_catalog(path=str(f))
    assert cat.records[0]["Identifier"] == "eos1"
