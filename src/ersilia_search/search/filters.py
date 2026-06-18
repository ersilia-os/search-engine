"""Structured filtering over the catalog.

Filter semantics:
- **AND across distinct fields** — a record must satisfy every field given.
- **OR within a field** — multiple accepted values for one field match if any
  applies; for a multi-valued record field, the record matches if its list
  intersects the accepted values.

This module is a pure matcher: it expects RAW field names already mapped from
query params, and the "default to Ready" rule is applied upstream (in the API
layer), not here.
"""

from ersilia_search.io import schema
from ersilia_search.io.loader import Catalog

_MULTI = set(schema.FIELD_GROUPS["multi"])


def apply_filters(catalog: Catalog, filters: dict[str, list[str]]) -> list[int]:
    """Return the indices of records passing all filters.

    Parameters
    ----------
    catalog : Catalog
        The catalog to filter.
    filters : dict[str, list[str]]
        Maps a RAW field name to its accepted values, e.g.
        ``{"Task": ["Annotation"], "Biomedical Area": ["Malaria"]}``. An empty
        mapping matches every record.

    Returns
    -------
    list[int]
        Indices into ``catalog.records`` that satisfy every field (values within
        a field are OR'd).
    """
    if not filters:
        return list(range(len(catalog.records)))

    accepted_sets = {field: set(values) for field, values in filters.items()}

    matched = []
    for i, record in enumerate(catalog.records):
        ok = True
        for field, accepted in accepted_sets.items():
            value = record.get(field)
            if field in _MULTI:
                if not accepted.intersection(value or []):
                    ok = False
                    break
            elif value not in accepted:
                ok = False
                break
        if ok:
            matched.append(i)
    return matched
