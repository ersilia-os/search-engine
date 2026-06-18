# Search engine for the Ersilia Model Hub

A small FastAPI service and CLI to search the [Ersilia Model Hub](https://github.com/ersilia-os/ersilia) catalog by keyword and structured filters. It returns ranked models as CSV, with an explanation of *why* each model matched.

The API reads the live model catalog from S3 at runtime (cached, refreshed daily), so results stay current without redeploying.

## Install

```bash
conda create -n ersilia-search python=3.12
conda activate ersilia-search
pip install git+https://github.com/ersilia-os/search-engine.git
```

For development (tests and running the API locally) install the dev extras from a clone:

```bash
pip install -e ".[dev]"
```

## CLI

Query the API and write ranked results as CSV:

```bash
ersilia_search --text "solubility" --task Annotation --limit 10 -o results.csv
```

| Option | Description |
|---|---|
| `--text, -t` | Free-text keyword query (drives ranking) |
| `--task` | Filter by task (repeatable) |
| `--subtask` | Filter by subtask (repeatable) |
| `--status` | Filter by status (repeatable; default: Ready only) |
| `--tag` | Filter by tag (repeatable) |
| `--biomedical-area` | Filter by biomedical area (repeatable) |
| `--target-organism` | Filter by target organism (repeatable) |
| `--all-statuses` | Include non-Ready models |
| `--limit` | Maximum results (default 50) |
| `--list-facets` | List valid filter values and exit |
| `-o, --output-file` | Write CSV to a file (default: stdout) |
| `--api-url` | API base URL (env: `ERSILIA_SEARCH_API_URL`) |

Filters combine as **AND across fields, OR within a field**: `--task Annotation --task Representation --biomedical-area Malaria` means *(Annotation or Representation) and Malaria*.

## API

Run locally (needs the `dev` extras for `uvicorn`):

```bash
uvicorn ersilia_search.api.app:app --reload
```

| Endpoint | Description |
|---|---|
| `GET /search` | Ranked, filtered models (JSON) |
| `GET /facets` | Valid values for each filterable field |
| `GET /healthz` | Health check and model count |

Interactive docs at `/docs`. The CLI defaults to `http://localhost:8000`; point it at the deployed service with `--api-url` or by setting `ERSILIA_SEARCH_API_URL`.

## About the Ersilia Open Source Initiative

The [Ersilia Open Source Initiative](https://ersilia.io) is a tech-nonprofit organization fueling sustainable research in the Global South. Ersilia's main asset is the [Ersilia Model Hub](https://github.com/ersilia-os/ersilia), an open-source repository of AI/ML models for antimicrobial drug discovery.

![Ersilia Logo](assets/Ersilia_Brand.png)
