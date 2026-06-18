"""Render API result rows as CSV text for the CLI."""

import csv
import io

from ersilia_search.io import schema

CSV_COLUMNS = schema.OUTPUT_FIELDS + ["score", "matched_keywords"]

_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _clean(value) -> str:
    """Flatten lists, stringify, and guard against spreadsheet formula injection."""
    if isinstance(value, list):
        value = "; ".join(str(v) for v in value)
    text = "" if value is None else str(value)
    if text and text[0] in _FORMULA_PREFIXES:
        text = "'" + text
    return text


def write_csv(results: list[dict]) -> str:
    """Serialize result rows to a CSV string with the curated columns.

    Parameters
    ----------
    results : list[dict]
        Rows from the API ``/search`` response.

    Returns
    -------
    str
        CSV text including a header row.
    """
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in results:
        writer.writerow({col: _clean(row.get(col)) for col in CSV_COLUMNS})
    return out.getvalue()
