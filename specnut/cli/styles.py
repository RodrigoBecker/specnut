"""Rich styling configurations for SpecNut CLI."""

from rich.console import Console
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
