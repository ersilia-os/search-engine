"""Configuration constants for ersilia-search.

Environment overrides (ERSILIA_SEARCH_DATA, ERSILIA_SEARCH_DATA_URL,
ERSILIA_SEARCH_CACHE_TTL, ERSILIA_SEARCH_API_URL) are read at the point of use
(in the loader and CLI), falling back to the defaults below.
"""

# --- Data source -----------------------------------------------------------
DEFAULT_DATA_URL = "https://ersilia-model-hub.s3.eu-central-1.amazonaws.com/models.json"
DEFAULT_CACHE_TTL = 86_400  # seconds (~24h) the in-memory catalog is considered fresh

# --- CLI -------------------------------------------------------------------
DEFAULT_API_URL = "https://search-engine-six-iota.vercel.app"  # deployed Vercel endpoint

# --- Ranking knobs ---------------------------------------------------------
FIELD_WEIGHTS = {
    "Title": 5.0,
    "Interpretation": 1.0,
    "Description": 2.0,
}
SUBSTRING_MIN_LEN = 4  # only try substring fallback for query terms this long or longer
COVERAGE_BONUS = 0.5  # weight of the "fraction of distinct query terms matched" bonus
ID_MATCH_WEIGHT = 100.0  # exact Identifier/Slug match floats to the top

# --- Result limits ---------------------------------------------------------
DEFAULT_LIMIT = 50
MAX_LIMIT = 500  # hard cap on results per request
