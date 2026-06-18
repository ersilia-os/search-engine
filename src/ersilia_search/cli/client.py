"""HTTP client the CLI uses to query the search API."""

import httpx


class ApiError(Exception):
    """Raised for a failed API call, carrying a user-facing message."""


def _search_query(params: dict) -> list[tuple[str, str]]:
    """Build a list of ``(key, value)`` query pairs (repeated keys for multi-filters)."""
    query: list[tuple[str, str]] = []
    if params.get("text"):
        query.append(("text", params["text"]))
    for key in (
        "task",
        "subtask",
        "status",
        "tag",
        "biomedical_area",
        "target_organism",
    ):
        for value in params.get(key, ()):
            query.append((key, value))
    if params.get("all_statuses"):
        query.append(("all_statuses", "true"))
    query.append(("limit", str(params["limit"])))
    return query


def _get(base_url: str, path: str, query=None):
    """GET ``base_url + path``, translating transport and 400 errors into ApiError."""
    url = f"{base_url.rstrip('/')}{path}"
    try:
        resp = httpx.get(url, params=query, timeout=30.0)
    except httpx.RequestError as exc:
        raise ApiError(
            f"Could not reach the API at {base_url} ({exc}). "
            f"Is the server running and --api-url correct?"
        ) from exc
    if resp.status_code == 400:
        raise ApiError(resp.json().get("detail", "Bad request"))
    resp.raise_for_status()
    return resp.json()


def search_models(base_url: str, params: dict) -> list[dict]:
    """Call ``GET /search`` and return the result rows."""
    return _get(base_url, "/search", _search_query(params))["results"]


def get_facets(base_url: str) -> dict[str, list[str]]:
    """Call ``GET /facets`` and return the field -> values mapping."""
    return _get(base_url, "/facets")
