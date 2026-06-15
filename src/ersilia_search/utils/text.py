"""Text tokenization shared by the search index and queries."""

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase ``text`` and split it into alphanumeric tokens.

    Parameters
    ----------
    text : str
        Raw text (a model field value or a user query).

    Returns
    -------
    list[str]
        Lowercased tokens; an empty list for ``None`` or empty input.
    """
    if not text:
        return []
    return _TOKEN_RE.findall(text.lower())
