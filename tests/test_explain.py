"""Tests for the explanation renderer."""

from ersilia_search.search.explain import explain


def test_empty_matches():
    assert explain({}) == ""


def test_count_format():
    assert explain({"Title": {"toxicity": 3}}) == 'Title: "toxicity"(x3)'


def test_fields_ordered_by_weight():
    # insertion order is Interpretation, Description, Title; output must be by weight
    out = explain(
        {
            "Interpretation": {"x": 1},
            "Description": {"x": 1},
            "Title": {"x": 1},
        }
    )
    assert out.index("Title") < out.index("Description") < out.index("Interpretation")


def test_identifier_listed_first():
    out = explain({"Title": {"natural": 1}, "Identifier": {"eos6tg8": 1}})
    assert out.startswith("Identifier:")
