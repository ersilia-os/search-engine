"""Keyword ranking: weighted term-frequency scoring over free-text fields.

The same ``matches`` structure drives both the score and the human-readable
explanation, so the two can never drift apart. An exact ``Identifier``/``Slug``
match adds a large flat boost so a direct lookup (e.g. ``eos6tg8``) always wins.
"""

import math

from ersilia_search import config

_WEIGHTS = config.FIELD_WEIGHTS


def score_record(
    record: dict,
    record_tokens: dict[str, list[str]],
    query_tokens: list[str],
) -> tuple[float, dict[str, dict[str, int]]]:
    """Score one record against the query.

    Parameters
    ----------
    record : dict
        The normalized record (used for the exact Identifier/Slug boost).
    record_tokens : dict[str, list[str]]
        Precomputed tokens per free-text field (``catalog.text_tokens[i]``).
    query_tokens : list[str]
        The tokenized query.

    Returns
    -------
    tuple[float, dict[str, dict[str, int]]]
        The score and a ``matches`` map ``{field: {term: count}}`` recording
        which query terms hit which fields, and how many times.
    """
    score = 0.0
    matches: dict[str, dict[str, int]] = {}

    if not query_tokens:
        return score, matches

    for field, weight in _WEIGHTS.items():
        tokens = record_tokens.get(field)
        if not tokens:
            continue
        token_set = set(tokens)
        field_matches: dict[str, int] = {}
        for term in query_tokens:
            if term in token_set:
                tf = tokens.count(term)
            elif len(term) >= config.SUBSTRING_MIN_LEN:
                tf = sum(1 for t in tokens if term in t)
            else:
                tf = 0
            if tf:
                score += weight * (1.0 + math.log(tf))
                field_matches[term] = field_matches.get(term, 0) + tf
        if field_matches:
            matches[field] = field_matches

    # Coverage bonus: reward hitting more distinct query terms.
    distinct_hit = len({term for fm in matches.values() for term in fm})
    distinct_query = len(set(query_tokens))
    score *= 1.0 + config.COVERAGE_BONUS * (distinct_hit / distinct_query)

    # Exact Identifier/Slug match floats a direct lookup to the top.
    query_set = set(query_tokens)
    full_query = " ".join(query_tokens)
    identifier = str(record.get("Identifier", "")).lower()
    slug = str(record.get("Slug", "")).lower()
    if identifier and identifier in query_set:
        score += config.ID_MATCH_WEIGHT
        matches.setdefault("Identifier", {})[identifier] = 1
    elif slug and " ".join(slug.replace("-", " ").split()) == full_query:
        score += config.ID_MATCH_WEIGHT
        matches.setdefault("Slug", {})[slug] = 1

    return score, matches
