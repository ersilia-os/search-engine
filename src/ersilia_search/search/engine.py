"""The one search entry point shared by the API and the CLI.

Orchestrates: filter the catalog, then (if a text query is given) rank the
survivors and attach an explanation. Returns full records plus the extra
``score``, ``matches`` and ``matched_keywords`` fields, leaving column curation
to the API / CSV layers.
"""

from ersilia_search.io.loader import Catalog
from ersilia_search.search.explain import explain
from ersilia_search.search.filters import apply_filters
from ersilia_search.search.ranking import score_record
from ersilia_search.utils.text import tokenize


def _year(record: dict) -> int:
    """Publication Year as an int for sorting (missing/invalid -> 0)."""
    try:
        return int(record.get("Publication Year") or 0)
    except (TypeError, ValueError):
        return 0


def _make_hit(record: dict, score: float | None, matches: dict) -> dict:
    """Build a result row: the record plus score/matches/explanation."""
    hit = dict(record)
    hit["score"] = round(score, 4) if score is not None else None
    hit["matches"] = matches
    hit["matched_keywords"] = explain(matches)
    return hit


def search(
    catalog: Catalog,
    filters: dict[str, list[str]] | None = None,
    text: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Filter, optionally rank by keyword, and return result rows.

    Parameters
    ----------
    catalog : Catalog
        The catalog to search.
    filters : dict[str, list[str]], optional
        RAW field name -> accepted values (AND across fields, OR within).
    text : str, optional
        Free-text query. When empty, results are filtered only and ordered by
        Publication Year (newest first), then Identifier.
    limit : int, optional
        Maximum number of rows to return; ``None`` returns all.

    Returns
    -------
    list[dict]
        Result rows, each the record plus ``score``, ``matches`` and
        ``matched_keywords``. When ranked, sorted by score descending; records
        that match no query term are dropped.
    """
    indices = apply_filters(catalog, filters or {})
    text = (text or "").strip()

    if not text:
        records = [catalog.records[i] for i in indices]
        records.sort(key=lambda r: (-_year(r), str(r.get("Identifier", ""))))
        hits = [_make_hit(r, None, {}) for r in records]
    else:
        query_tokens = tokenize(text)
        scored = []
        for i in indices:
            score, matches = score_record(
                catalog.records[i], catalog.text_tokens[i], query_tokens
            )
            if score > 0:
                scored.append((score, catalog.records[i], matches))
        scored.sort(key=lambda t: (-t[0], str(t[1].get("Identifier", ""))))
        hits = [_make_hit(r, s, m) for s, r, m in scored]

    return hits if limit is None else hits[:limit]
