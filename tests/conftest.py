"""Shared pytest fixtures.

The catalog is loaded once from the committed JSON fixture via an explicit
``path`` — this bypasses the network and the in-memory cache entirely.
"""

import os

import pytest

from ersilia_search.io.loader import get_catalog

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "models_sample.json")


@pytest.fixture(scope="session")
def catalog():
    """The 7-record sample catalog, loaded from the fixture file."""
    return get_catalog(path=FIXTURE)
