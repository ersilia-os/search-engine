"""HTTP routes: keyword/filter search, facet discovery, and a health check."""

from fastapi import APIRouter, Query

from ersilia_search import config
from ersilia_search.api.params import build_filters
from ersilia_search.io import schema
from ersilia_search.io.loader import get_catalog
from ersilia_search.search.engine import search

router = APIRouter()


def _serialize(hit: dict) -> dict:
    """Project a result row to the curated output fields plus search extras."""
    row = {field: hit.get(field) for field in schema.OUTPUT_FIELDS}
    row["score"] = hit["score"]
    row["matched_keywords"] = hit["matched_keywords"]
    row["matches"] = hit["matches"]
    return row


@router.get("/search")
def search_models(
    text: str | None = Query(None, description="Free-text keyword query"),
    task: list[str] = Query(default=[]),
    subtask: list[str] = Query(default=[]),
    status: list[str] = Query(default=[]),
    tag: list[str] = Query(default=[]),
    biomedical_area: list[str] = Query(default=[]),
    target_organism: list[str] = Query(default=[]),
    all_statuses: bool = Query(False, description="Include non-Ready models"),
    limit: int = Query(config.DEFAULT_LIMIT, ge=1, le=config.MAX_LIMIT),
):
    """Filter and (if ``text`` is given) rank models; return ranked JSON rows."""
    catalog = get_catalog()
    params = {
        "task": task,
        "subtask": subtask,
        "status": status,
        "tag": tag,
        "biomedical_area": biomedical_area,
        "target_organism": target_organism,
    }
    filters = build_filters(catalog, params, all_statuses=all_statuses)
    hits = search(catalog, filters=filters, text=text, limit=limit)
    return {"count": len(hits), "results": [_serialize(h) for h in hits]}


@router.get("/facets")
def facets():
    """Return the distinct values available for each filterable field."""
    return get_catalog().facets


@router.get("/healthz")
def healthz():
    """Liveness check with the loaded model count."""
    return {"status": "ok", "models": len(get_catalog().records)}
