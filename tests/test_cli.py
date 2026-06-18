"""Tests for the CLI: CSV rendering, query building, and the command itself."""

from click.testing import CliRunner

import ersilia_search.cli.create_cli as cli_mod
from ersilia_search.cli.client import ApiError, _search_query
from ersilia_search.cli.create_cli import cli
from ersilia_search.io.csv_writer import CSV_COLUMNS, write_csv


# --- csv_writer ------------------------------------------------------------


def test_csv_header_and_list_join():
    out = write_csv([{"Identifier": "eos1", "Tag": ["A", "B"]}])
    assert out.splitlines()[0] == ",".join(CSV_COLUMNS)
    assert "A; B" in out


def test_csv_formula_injection_guard():
    assert "'=danger" in write_csv([{"Title": "=danger"}])


def test_csv_none_becomes_blank():
    assert "None" not in write_csv([{"Identifier": "eos1"}])  # score=None etc.


# --- query builder ---------------------------------------------------------


def test_search_query_repeats_and_flags():
    q = _search_query(
        {
            "text": "tox",
            "task": ("Annotation", "Representation"),
            "all_statuses": True,
            "limit": 5,
        }
    )
    assert ("text", "tox") in q
    assert ("task", "Annotation") in q and ("task", "Representation") in q
    assert ("all_statuses", "true") in q
    assert ("limit", "5") in q


# --- command (HTTP layer mocked) -------------------------------------------


def test_cli_outputs_csv(monkeypatch):
    monkeypatch.setattr(
        cli_mod,
        "search_models",
        lambda base, params: [
            {"Identifier": "eos8g50", "score": 12.0, "matched_keywords": "x"}
        ],
    )
    res = CliRunner().invoke(
        cli, ["--text", "solubility", "--csv", "--api-url", "http://x"]
    )
    assert res.exit_code == 0
    assert res.output.splitlines()[0].startswith("Identifier,")
    assert "eos8g50" in res.output


def test_cli_default_table_output(monkeypatch):
    monkeypatch.setattr(
        cli_mod,
        "search_models",
        lambda base, params: [
            {
                "Identifier": "eos8g50",
                "Title": "FASTSOLV",
                "score": 12.0,
                "matched_keywords": "x",
            }
        ],
    )
    res = CliRunner().invoke(cli, ["--text", "solubility", "--api-url", "http://x"])
    assert res.exit_code == 0
    assert "eos8g50" in res.output  # rendered in the Rich table
    assert not res.output.startswith("Identifier,")  # not raw CSV


def test_cli_list_facets(monkeypatch):
    monkeypatch.setattr(
        cli_mod, "get_facets", lambda base: {"Task": ["Annotation", "Sampling"]}
    )
    res = CliRunner().invoke(cli, ["--list-facets", "--api-url", "http://x"])
    assert res.exit_code == 0
    assert "Task" in res.output and "Annotation" in res.output


def test_cli_api_error_exits_nonzero(monkeypatch):
    def boom(base, params):
        raise ApiError("bad value")

    monkeypatch.setattr(cli_mod, "search_models", boom)
    res = CliRunner().invoke(cli, ["--task", "X", "--api-url", "http://x"])
    assert res.exit_code == 1
