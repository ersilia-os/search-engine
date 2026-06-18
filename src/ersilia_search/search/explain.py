"""Render a ``matches`` map into the human-readable ``matched_keywords`` string.

Fields are ordered by signal strength: an exact Identifier/Slug match first,
then free-text fields by descending weight (Title, Description, Interpretation).
"""

from ersilia_search import config

_ID_FIELDS = ["Identifier", "Slug"]
_WEIGHTED_ORDER = [
    field
    for field, _ in sorted(
        config.FIELD_WEIGHTS.items(), key=lambda kv: kv[1], reverse=True
    )
]


def _field_order(field: str) -> tuple[int, object]:
    """Sort key: ID fields first, then free-text by weight, then anything else."""
    if field in _ID_FIELDS:
        return (0, _ID_FIELDS.index(field))
    if field in _WEIGHTED_ORDER:
        return (1, _WEIGHTED_ORDER.index(field))
    return (2, field)


def explain(matches: dict[str, dict[str, int]]) -> str:
    """Render a matches map into a compact, ordered explanation string.

    Parameters
    ----------
    matches : dict[str, dict[str, int]]
        ``{field: {term: count}}`` as produced by ``ranking.score_record``.

    Returns
    -------
    str
        e.g. ``'Title: "solubility"(x1); Description: "solubility"(x1)'``;
        an empty string when there are no matches.
    """
    if not matches:
        return ""
    parts = []
    for field in sorted(matches, key=_field_order):
        rendered = ", ".join(
            f'"{term}"(x{count})' for term, count in matches[field].items()
        )
        parts.append(f"{field}: {rendered}")
    return "; ".join(parts)
