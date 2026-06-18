"""The ``ersilia_search`` command: query the API and emit ranked models as CSV."""

import os
import sys

import click

from ersilia_search import config
from ersilia_search.cli.client import ApiError, get_facets, search_models
from ersilia_search.cli.display import print_facets_table, print_results_table
from ersilia_search.io.csv_writer import write_csv
from ersilia_search.utils.logging import logger
from ersilia_search.utils.text import tokenize


@click.command()
@click.option("--text", "-t", default=None, help="Free-text keyword query.")
@click.option("--task", multiple=True, help="Filter by task (repeatable).")
@click.option("--subtask", multiple=True, help="Filter by subtask (repeatable).")
@click.option("--status", multiple=True, help="Filter by status (repeatable).")
@click.option("--tag", multiple=True, help="Filter by tag (repeatable).")
@click.option(
    "--biomedical-area", multiple=True, help="Filter by biomedical area (repeatable)."
)
@click.option(
    "--target-organism", multiple=True, help="Filter by target organism (repeatable)."
)
@click.option(
    "--all-statuses",
    is_flag=True,
    help="Include non-Ready models (default: Ready only).",
)
@click.option(
    "--limit", default=config.DEFAULT_LIMIT, show_default=True, help="Max results."
)
@click.option(
    "--api-url", default=None, help="API base URL (env: ERSILIA_SEARCH_API_URL)."
)
@click.option(
    "-o",
    "--output-file",
    type=click.Path(),
    default=None,
    help="Write CSV here (default: stdout).",
)
@click.option(
    "--csv", "as_csv", is_flag=True, help="Print raw CSV to stdout (for piping)."
)
@click.option("--list-facets", is_flag=True, help="List valid filter values and exit.")
def cli(
    text,
    task,
    subtask,
    status,
    tag,
    biomedical_area,
    target_organism,
    all_statuses,
    limit,
    api_url,
    output_file,
    as_csv,
    list_facets,
):
    """Search the Ersilia Model Hub and output ranked models as CSV."""
    base_url = api_url or os.environ.get(
        "ERSILIA_SEARCH_API_URL", config.DEFAULT_API_URL
    )

    try:
        if list_facets:
            print_facets_table(get_facets(base_url))
            return
        results = search_models(
            base_url,
            {
                "text": text,
                "task": task,
                "subtask": subtask,
                "status": status,
                "tag": tag,
                "biomedical_area": biomedical_area,
                "target_organism": target_organism,
                "all_statuses": all_statuses,
                "limit": limit,
            },
        )
    except ApiError as exc:
        logger.error(str(exc))
        sys.exit(1)

    if output_file:
        with open(output_file, "w", newline="") as f:
            f.write(write_csv(results))
        logger.success(f"Wrote {len(results)} rows → {output_file}")
    elif as_csv:
        click.echo(write_csv(results), nl=False)
    else:
        # highlight the text query words plus every filter value across the table
        highlight_terms = tokenize(text or "")
        for values in (task, subtask, status, tag, biomedical_area, target_organism):
            highlight_terms.extend(values)
        print_results_table(results, highlight_terms)
