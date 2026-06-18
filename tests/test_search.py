"""Behavioral tests for the search core, run against the committed fixture."""

from ersilia_search import config
from ersilia_search.search.engine import search


def ids(hits):
    return [h["Identifier"] for h in hits]


# --- ranking ---------------------------------------------------------------


def test_keyword_ranking_title_wins(catalog):
    hits = search(catalog, text="solubility")
    assert hits[0]["Identifier"] == "eos8g50"  # "solubility" in the title (weight 5)
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)  # descending


def test_zero_score_dropped(catalog):
    assert search(catalog, text="zzzznotarealword") == []


def test_explanation_faithful(catalog):
    top = search(catalog, text="solubility")[0]
    assert "Title" in top["matched_keywords"]
    assert "solubility" in top["matched_keywords"]
    # every field reported in matches actually carries the matched term(s)
    assert all(terms for terms in top["matches"].values())


def test_id_boost(catalog):
    hits = search(catalog, text="eos6tg8")
    assert hits[0]["Identifier"] == "eos6tg8"
    assert hits[0]["score"] >= config.ID_MATCH_WEIGHT


# --- filtering -------------------------------------------------------------


def test_filter_single_field(catalog):
    assert ids(search(catalog, filters={"Task": ["Sampling"]})) == ["eos8vud"]


def test_filter_multi_or(catalog):
    got = set(ids(search(catalog, filters={"Biomedical Area": ["Malaria"]})))
    assert got == {"eos7kpb", "eos9n1s"}


def test_filter_and_across_fields(catalog):
    got = ids(search(catalog, filters={"Task": ["Annotation"], "Status": ["Archived"]}))
    assert got == ["eos5dti"]


def test_filter_and_no_overlap_is_empty(catalog):
    # the Sampling model's Biomedical Area is "Any", not Malaria -> nothing satisfies both
    assert (
        search(catalog, filters={"Task": ["Sampling"], "Biomedical Area": ["Malaria"]})
        == []
    )


def test_status_ready_excludes_archived(catalog):
    assert "eos5dti" not in ids(search(catalog, filters={"Status": ["Ready"]}))


def test_no_filter_includes_archived(catalog):
    # the engine does NOT inject default-Ready; that is the API layer's job
    assert "eos5dti" in ids(search(catalog, filters={}))


# --- ordering & limit ------------------------------------------------------


def test_no_text_sorted_by_year(catalog):
    hits = search(catalog, filters={})
    years = [int(h.get("Publication Year") or 0) for h in hits]
    assert years == sorted(years, reverse=True)
    assert all(h["score"] is None for h in hits)


def test_limit(catalog):
    assert len(search(catalog, limit=2)) == 2


def test_limit_exceeding_returns_all(catalog):
    assert len(search(catalog, limit=999)) == 7


# --- query handling --------------------------------------------------------


def test_case_insensitive(catalog):
    assert search(catalog, text="SOLUBILITY")[0]["Identifier"] == "eos8g50"


def test_substring_fallback_matches(catalog):
    # "solub" (>= 4 chars) matches "solubility" via the substring fallback
    assert "eos8g50" in ids(search(catalog, text="solub"))


def test_short_term_has_no_substring_fallback(catalog):
    # "sol" is below SUBSTRING_MIN_LEN (4): no substring fallback, so no match
    assert "eos8g50" not in ids(search(catalog, text="sol"))


def test_multiword_coverage_bonus(catalog):
    # eos8g50 hits both terms ("solubility prediction" is in its title)
    assert search(catalog, text="solubility prediction")[0]["Identifier"] == "eos8g50"


def test_combined_filter_and_text(catalog):
    hits = search(catalog, filters={"Biomedical Area": ["Malaria"]}, text="inhibitor")
    assert "eos9n1s" in ids(hits)  # Hemozoin inhibitor
    assert all("Malaria" in h["Biomedical Area"] for h in hits)  # filter still enforced
