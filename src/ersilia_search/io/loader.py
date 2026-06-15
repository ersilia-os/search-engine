"""Load the model catalog from the public S3 URL (or a local override)."""

import json
import os
import time
from dataclasses import dataclass

import httpx

from ersilia_search import config
from ersilia_search.io import schema
from ersilia_search.utils.logging import logger
from ersilia_search.utils.text import tokenize


@dataclass
class Catalog:
    records: list[dict]  # normalized, raw keys preserved
    text_tokens: list[dict[str, list[str]]]  # per record: {free_text field: tokens}
    facets: dict[str, list[str]]  # per filterable field: sorted distinct values


def normalize(raw: dict) -> dict:
    """Return a copy of ``raw`` with consistent types.

    Multi-valued fields are forced to lists and text fields to strings, so the
    rest of the code never has to guard against ``None`` or stray scalars. Keys
    are left untouched (raw spelling preserved); unknown fields pass through so
    they remain available as output columns.
    """
    rec = dict(raw)
    for field in schema.FIELD_GROUPS["multi"]:
        val = rec.get(field)
        if val is None:
            rec[field] = []
        elif not isinstance(val, list):
            rec[field] = [val]
    for field in (
        schema.FIELD_GROUPS["free_text"]
        + schema.FIELD_GROUPS["single"]
        + schema.FIELD_GROUPS["identifier"]
    ):
        if rec.get(field) is None:
            rec[field] = ""
    return rec


def build_catalog(records: list[dict]) -> Catalog:
    """Normalize records, precompute free-text tokens, and collect facets.

    Pure function (no network, no env) — the unit-test entry point.

    Parameters
    ----------
    records : list[dict]
        Raw model records parsed from ``models.json``.

    Returns
    -------
    Catalog
        The in-memory, search-ready catalog.
    """
    norm = [normalize(r) for r in records]

    text_tokens = [
        {field: tokenize(rec[field]) for field in schema.FIELD_GROUPS["free_text"]}
        for rec in norm
    ]

    facets: dict[str, list[str]] = {}
    for field in schema.FIELD_GROUPS["single"] + schema.FIELD_GROUPS["multi"]:
        values: set[str] = set()
        for rec in norm:
            val = rec.get(field)
            if isinstance(val, list):
                values.update(v for v in val if v)
            elif val:
                values.add(val)
        facets[field] = sorted(values)

    return Catalog(records=norm, text_tokens=text_tokens, facets=facets)


# --- In-memory cache for the running API ----------------------------------
_cache: Catalog | None = None
_fetched_at: float = 0.0
_etag: str | None = None


def _fetch(url: str, etag: str | None) -> tuple[list[dict] | None, str | None]:
    """GET ``url`` with a conditional ``If-None-Match``.

    Returns ``(records, etag)``. ``records`` is ``None`` when the server
    answers ``304 Not Modified`` (the cached copy is still current).
    """
    headers = {"If-None-Match": etag} if etag else {}
    resp = httpx.get(url, headers=headers, timeout=30.0)
    if resp.status_code == 304:
        return None, etag
    resp.raise_for_status()
    return resp.json(), resp.headers.get("ETag")


def get_catalog(path: str | None = None, url: str | None = None) -> Catalog:
    """Return the catalog, fetching/refreshing from S3 as needed.

    A local file (``path`` argument or ``ERSILIA_SEARCH_DATA`` env var) bypasses
    the network and the cache entirely — used by tests and offline runs.
    Otherwise the catalog is fetched from ``url`` (or ``ERSILIA_SEARCH_DATA_URL``,
    defaulting to ``config.DEFAULT_DATA_URL``) and cached in memory; it is only
    refetched once the cache is older than the TTL, and a conditional request
    avoids re-downloading unchanged data. If a refresh fails but a cached copy
    exists, the stale copy is served rather than erroring.
    """
    global _cache, _fetched_at, _etag

    path = path or os.environ.get("ERSILIA_SEARCH_DATA")
    if path:
        with open(path) as f:
            return build_catalog(json.load(f))

    url = url or os.environ.get("ERSILIA_SEARCH_DATA_URL", config.DEFAULT_DATA_URL)
    ttl = int(os.environ.get("ERSILIA_SEARCH_CACHE_TTL", config.DEFAULT_CACHE_TTL))

    now = time.time()
    if _cache is not None and (now - _fetched_at) < ttl:
        return _cache

    try:
        records, new_etag = _fetch(url, _etag)
        if records is None:  # 304 Not Modified — keep cached data
            _fetched_at = now
            return _cache
        _cache = build_catalog(records)
        _etag = new_etag
        _fetched_at = now
        logger.success(f"Loaded {len(_cache.records)} models from {url}")
        return _cache
    except Exception as exc:
        if _cache is not None:
            logger.warning(f"Catalog refresh failed ({exc}); serving cached copy")
            return _cache
        raise
