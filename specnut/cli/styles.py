"""Rich styling configurations for SpecNut CLI."""

from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.theme import Theme

# Custom theme for SpecNut
specnut_theme = Theme(
    {
        "success": "bold green",
        "error": "bold red",
        "warning": "bold yellow",
        "info": "cyan",
        "highlight": "bold cyan",
        "metric": "green",
        "path": "blue underline",
    }
)

# Console with custom theme
themed_console = Console(theme=specnut_theme)

# Export console for use by other modules
console = themed_console


def print_success(message: str):
    """Print success message."""
    themed_console.print(f"✓ {message}", style="success")


def print_error(error_type: str, message: str, suggestion: str | None = None):
    """Print error message with optional suggestion.

    Args:
        error_type: Type of error (e.g., "File Not Found")
        message: Specific error message
        suggestion: Optional suggestion for how to fix
    """
    themed_console.print(f"\n✗ Error: {error_type}", style="error")
    themed_console.print(f"  → {message}")

    if suggestion:
        themed_console.print(f"\nSuggestion: {suggestion}", style="info")
    themed_console.print()


def print_warning(message: str):
    """Print warning message."""
    themed_console.print(f"⚠ {message}", style="warning")


def print_info(message: str):
    """Print info message."""
    themed_console.print(message, style="info")


# ============================================================================
# Batch Processing Display Functions (Feature: 002-directory-digest)
# ============================================================================


def display_batch_summary(summary, dry_run: bool = False):
    """Display batch processing summary with Rich table.

    Args:
        summary: ProcessingSummary with aggregate results
        dry_run: Whether this was a dry-run (preview mode)
    """
    from rich import box

    from specnut.models.metrics import ProcessingStatus

    table = Table(
        title="Batch Processing Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    # Define columns
    table.add_column("File", style="cyan", no_wrap=False)
    table.add_column("Status", justify="center", width=12)
    table.add_column("Original", justify="right", width=10)
    table.add_column("Digest", justify="right", width=10)
    table.add_column("Saved", justify="right", width=8)

    # Add rows for each file
    for result in summary.results:
        if result.status == ProcessingStatus.SUCCESS:
            status = "[green]✓ Success[/green]"
            orig = f"{result.original_tokens:,}"
            digest = f"{result.digest_tokens:,}"
            saved = f"{result.compression_ratio:.1%}"
        elif result.status == ProcessingStatus.SKIPPED:
            status = "[yellow]⊘ Skipped[/yellow]"
            orig = f"{result.original_tokens:,}" if result.original_tokens > 0 else "-"
            digest = f"{result.digest_tokens:,}" if result.digest_tokens > 0 else "-"
            saved = "-"
        else:  # FAILED
            status = "[red]✗ Failed[/red]"
            orig = digest = saved = "-"

        # Get relative path for cleaner display
        try:
            file_display = str(result.file_path.relative_to(Path.cwd()))
        except ValueError:
            file_display = str(result.file_path)

        table.add_row(file_display, status, orig, digest, saved)

    # Add aggregate summary row
    table.add_section()

    summary_label = f"TOTAL ({summary.successful_count} successful"
    if summary.failed_count > 0:
        summary_label += f", {summary.failed_count} failed"
    if summary.skipped_count > 0:
        summary_label += f", {summary.skipped_count} skipped"
    summary_label += ")"

    table.add_row(
        summary_label,
        "",
        f"{summary.total_original_tokens:,}",
        f"{summary.total_digest_tokens:,}",
        (
            f"{summary.average_compression_ratio:.1%}"
            if summary.successful_count > 0
            else "-"
        ),
    )

    # Print table
    console.print(table)

    # Show failed files detail
    if summary.has_failures:
        console.print("\n[bold red]Failed Files:[/bold red]")
        for result in summary.get_failed_files():
            console.print(
                f"  [red]{result.file_path}[/red]: {result.error_type}: {result.error_message}"
            )

    # Show skipped files if any
    skipped = [r for r in summary.results if r.status == ProcessingStatus.SKIPPED]
    if skipped:
        console.print("\n[bold yellow]Skipped Files:[/bold yellow]")
        for result in skipped:
            console.print(f"  [yellow]{result.file_path}[/yellow]: {result.error_message}")

    # Dry-run notice
    if dry_run:
        console.print("\n[dim]Note: This was a dry run. No files were modified.[/dim]")
