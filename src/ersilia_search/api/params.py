"""Translate query parameters into engine filters.

Maps snake_case params to raw field names, validates each value against the
catalog's known facet values (raising 400 on anything unknown), and applies the
default "Ready only" rule unless the caller opts out with ``all_statuses``.
"""

from fastapi import HTTPException

from ersilia_search.io import schema
from ersilia_search.io.loader import Catalog

DEFAULT_STATUS = ["Ready"]


def build_filters(
    catalog: Catalog,
    params: dict[str, list[str]],
    all_statuses: bool = False,
) -> dict[str, list[str]]:
    """Build a validated ``{raw field: values}`` filter map for the engine.

    Parameters
    ----------
    catalog : Catalog
        Used to validate values against ``catalog.facets``.
    params : dict[str, list[str]]
        snake_case param name -> requested values (empty lists are ignored).
    all_statuses : bool
        When False and no status was given, restrict results to "Ready".

    Returns
    -------
    dict[str, list[str]]
        Raw-field filters ready for ``engine.search``.

    Raises
    ------
    HTTPException
        400 if any value is not a known facet value for its field.
    """
    filters: dict[str, list[str]] = {}
    for param, values in params.items():
        if not values:
            continue
        raw_field = schema.PARAM_TO_RAW[param]
        valid = set(catalog.facets.get(raw_field, []))
        unknown = [v for v in values if v not in valid]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid value(s) for '{param}': {unknown}. "
                f"Valid values: {sorted(valid)}",
            )
        filters[raw_field] = list(values)

    if "Status" not in filters and not all_statuses:
        filters["Status"] = DEFAULT_STATUS

    return filters
