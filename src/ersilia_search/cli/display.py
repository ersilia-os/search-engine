"""Pretty terminal rendering of search results and facets via Rich tables."""

from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()

# Bold + underline keeps the terminal's own text colour, so matches stay
# legible on both light and dark themes without a loud background block.
HIGHLIGHT_STYLE = "bold underline"


def _highlight(text: str, terms: list[str]) -> Text:
    """Return Rich ``Text`` for ``text`` with every search term emphasized."""
    rich_text = Text(text or "")
    if terms:
        rich_text.highlight_words(terms, HIGHLIGHT_STYLE, case_sensitive=False)
    return rich_text


def print_results_table(
    results: list[dict], highlight_terms: list[str] | None = None
) -> None:
    """Render search results as a readable table with search terms highlighted.

    ``highlight_terms`` are the words to emphasize (the text query plus all filter
    values), applied across every cell. Shows a curated subset of columns; the
    full set is available via CSV output (``-o``/``--csv``).
    """
    if not results:
        console.print("[yellow]No models matched your query.[/yellow]")
        return

    terms = highlight_terms or []
    table = Table(header_style="bold cyan")
    table.add_column("ID", no_wrap=True)
    table.add_column("Title", max_width=30)
    table.add_column("Description", max_width=60)
    table.add_column("Task", no_wrap=True)
    table.add_column("Biomed. area", max_width=18)

    for r in results:
        table.add_row(
            _highlight(r.get("Identifier", ""), terms),
            _highlight(r.get("Title", ""), terms),
            _highlight(r.get("Description", ""), terms),
            _highlight(r.get("Task", ""), terms),
            _highlight("; ".join(r.get("Biomedical Area") or []), terms),
        )

    console.print(table)
    console.print(f"[dim]{len(results)} result(s)[/dim]")


def print_facets_table(facets: dict[str, list[str]]) -> None:
    """Render the available filter values, one field per row."""
    table = Table(header_style="bold cyan")
    table.add_column("Field", no_wrap=True, style="bold")
    table.add_column("Valid values")
    for field, values in facets.items():
        table.add_row(field, ", ".join(values))
    console.print(table)
