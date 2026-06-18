"""Smoke tests for the HTTP API, exercised in-process via TestClient."""

import os

import pytest
from fastapi.testclient import TestClient

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "models_sample.json")


@pytest.fixture
def client(monkeypatch):
    """A TestClient backed by the committed fixture (no network)."""
    monkeypatch.setenv("ERSILIA_SEARCH_DATA", FIXTURE)
    from ersilia_search.api.app import app

    return TestClient(app)


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "models": 7}


def test_search_ranks_and_explains(client):
    top = client.get("/search", params={"text": "solubility"}).json()["results"][0]
    assert top["Identifier"] == "eos8g50"
    assert "solubility" in top["matched_keywords"]


def test_default_ready_excludes_archived(client):
    ids = [x["Identifier"] for x in client.get("/search").json()["results"]]
    assert "eos5dti" not in ids


def test_all_statuses_includes_archived(client):
    r = client.get("/search", params={"all_statuses": "true"}).json()
    assert "eos5dti" in [x["Identifier"] for x in r["results"]]


def test_multi_or_filter(client):
    r = client.get("/search", params={"biomedical_area": "Malaria"}).json()
    assert sorted(x["Identifier"] for x in r["results"]) == ["eos7kpb", "eos9n1s"]


def test_bad_filter_value_returns_400(client):
    r = client.get("/search", params={"task": "Nonsense"})
    assert r.status_code == 400
    assert "Valid values" in r.json()["detail"]


def test_facets_endpoint(client):
    facets = client.get("/facets").json()
    assert "Annotation" in facets["Task"]
    assert "Ready" in facets["Status"]
