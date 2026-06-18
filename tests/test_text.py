"""Tests for the shared tokenizer."""

from ersilia_search.utils.text import tokenize


def test_lowercases():
    assert tokenize("Toxicity") == ["toxicity"]


def test_splits_on_punctuation_and_hyphens():
    assert tokenize("Antimicrobial resistance (AMR)") == [
        "antimicrobial",
        "resistance",
        "amr",
    ]
    assert tokenize("drug-likeness") == ["drug", "likeness"]
    assert tokenize("TP53/BRCA1") == ["tp53", "brca1"]


def test_keeps_digits_and_alphanumerics():
    assert tokenize("eos6tg8") == ["eos6tg8"]


def test_empty_and_none():
    assert tokenize("") == []
    assert tokenize(None) == []
    assert tokenize("   !!!  ") == []
