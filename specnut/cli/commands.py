"""Main CLI commands for SpecNut."""

import json
import sys
from typing import Optional

import typer
from rich.console import Console

from specnut import __version__
from specnut.cli.exit_codes import ExitCode

# Create Typer app
app = typer.Typer(
    name="specnut",
    help="CLI tool for optimizing specification digests to reduce token consumption",
    add_completion=False,
)

# Create Rich console for styled output
console = Console()

# Global state for verbose and debug modes
_verbose = False
_debug = False
_no_color = False


def version_callback(value: bool):
    """Callback for --version flag."""
    if value:
        console.print(f"SpecNut v{__version__}")
        raise typer.Exit(ExitCode.SUCCESS)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode with detailed traces",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable Rich styling (plain text output)",
    ),
):
    """SpecNut: Optimize specification digests to reduce token consumption.

    Use 'specnut COMMAND --help' for more information on a specific command.
    """
    global _verbose, _debug, _no_color
    _verbose = verbose
    _debug = debug
    _no_color = no_color

    if _no_color:
        console._force_terminal = False


@app.command()
def version(
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format (text or json)",
    )
):
    """Show version information."""
    try:
        # Get dependency versions
        import tiktoken
        import typer as typer_module
        import yaml
        from importlib.metadata import version as get_version

        deps = {
            "typer": getattr(typer_module, "__version__", get_version("typer")),
            "tiktoken": getattr(tiktoken, "__version__", get_version("tiktoken")),
            "rich": get_version("rich"),
            "pyyaml": getattr(yaml, "__version__", get_version("pyyaml")),
        }
    except (ImportError, Exception):
        deps = {}

    if format == "json":
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        output = {
            "specnut_version": __version__,
            "python_version": python_ver,
            "dependencies": deps,
            "digest_format_version": "1.0",
        }
        console.print(json.dumps(output, indent=2))
    else:
        console.print(f"[bold cyan]SpecNut[/bold cyan] v{__version__}\n")
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        console.print(f"Python:      {python_ver}")

        if deps:
            console.print(f"Typer:       {deps.get('typer', 'unknown')}")
            console.print(f"tiktoken:    {deps.get('tiktoken', 'unknown')}")
            console.print(f"Rich:        {deps.get('rich', 'unknown')}")
            console.print(f"PyYAML:      {deps.get('pyyaml', 'unknown')}")

        console.print("\nDigest Format: v1.0")

    sys.exit(ExitCode.SUCCESS)


@app.command()
def digest(
    input_file: str = typer.Argument(
        ..., help="Path to specification file (YAML, JSON, or Markdown)"
    ),
    output_file: Optional[str] = typer.Argument(None, help="Path for digest output (optional)"),
    format: str = typer.Option(
        "auto",
        "--format",
        "-f",
        help="Output format (auto/yaml/json/markdown/compact)",
    ),
    compression: str = typer.Option(
        "medium",
        "--compression",
        "-c",
        help="Compression level (low/medium/high)",
    ),
    show_metrics: bool = typer.Option(
        False,
        "--show-metrics",
        "-m",
        help="Display metrics after generation",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Show what would be done without writing output",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing digest file without prompting",
    ),
):
    """Generate optimized specification digest.

    Reads a specification file, applies compression to reduce token count
    by 30%+ while preserving critical information, and writes an optimized digest.

    Examples:

        # Basic usage
        specnut digest spec.md

        # With custom output
        specnut digest spec.yaml -f json -o digest.json

        # High compression with metrics
        specnut digest spec.md -c high -m

        # Preview without writing
        specnut digest spec.md --dry-run
    """
    from pathlib import Path

    from rich.progress import Progress, SpinnerColumn, TextColumn

    from specnut.cli.styles import print_error, print_info, print_success, print_warning
    from specnut.core.optimizer import generate_digest
    from specnut.models import CompressionLevel, FormatEnum
    from specnut.models.optimization import DEFAULT_PROFILE, OptimizationProfile
    from specnut.models.specification import Specification

    try:
        # Validate input file
        input_path = Path(input_file)
        if not input_path.exists():
            print_error(
                "File Not Found",
                f"{input_file} does not exist",
                "Check the file path and try again",
            )
            sys.exit(ExitCode.GENERAL_ERROR)

        if not input_path.is_file():
            print_error(
                "Invalid Input",
                f"{input_file} is not a file",
                "Provide a path to a file, not a directory",
            )
            sys.exit(ExitCode.GENERAL_ERROR)

        # Validate format
        try:
            if format == "auto":
                output_format = None  # Use same as input
            else:
                output_format = FormatEnum(format.lower())
        except ValueError:
            print_error(
                "Unsupported Format",
                f"Format '{format}' is not supported",
                "Use one of: auto, yaml, json, markdown, compact",
            )
            sys.exit(ExitCode.VALIDATION_ERROR)

        # Validate compression level
        try:
            compression_level = CompressionLevel(compression.lower())
        except ValueError:
            print_error(
                "Invalid Compression Level",
                f"Compression level '{compression}' is not valid",
                "Use one of: low, medium, high",
            )
            sys.exit(ExitCode.VALIDATION_ERROR)

        # Create optimization profile based on compression level
        if compression_level == CompressionLevel.LOW:
            profile = OptimizationProfile(
                name="low",
                compression_level=compression_level,
                target_reduction=0.32,
                section_priorities=DEFAULT_PROFILE.section_priorities,
                preserve_rules=DEFAULT_PROFILE.preserve_rules,
                abbreviation_map=None,  # No abbreviations for low compression
            )
        elif compression_level == CompressionLevel.HIGH:
            profile = OptimizationProfile(
                name="high",
                compression_level=compression_level,
                target_reduction=0.60,
                section_priorities=DEFAULT_PROFILE.section_priorities,
                preserve_rules=DEFAULT_PROFILE.preserve_rules,
                abbreviation_map=DEFAULT_PROFILE.abbreviation_map,
            )
        else:
            profile = DEFAULT_PROFILE

        # Load specification
        if _verbose or _debug:
            print_info(f"Loading specification from: {input_path}")

        spec = Specification.from_file(input_path)

        if _debug:
            print_info(f"File size: {spec.file_size_bytes:,} bytes")
            print_info(f"Format detected: {spec.format.value}")
            print_info(f"Original tokens: {spec.token_count:,}")

        # Generate digest
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating digest...", total=None)
            digest_obj, metrics = generate_digest(spec, profile, output_format)
            progress.remove_task(task)

        # Check compression ratio
        if not digest_obj.validate_compression_ratio():
            savings = digest_obj.calculate_savings()
            ratio = digest_obj.compression_ratio
            print_warning(
                f"Could not achieve minimum 30% token reduction\n"
                f"  Original: {spec.token_count:,} tokens\n"
                f"  Digest:   {digest_obj.token_count:,} tokens\n"
                f"  Saved:    {savings:,} tokens ({ratio:.1%})\n\n"
                f"This file may already be optimized or contain mostly critical content."
            )
            sys.exit(ExitCode.COMPRESSION_ERROR)

        # Determine output path
        if output_file:
            output_path = Path(output_file)
        else:
            # Default: INPUT.digest.EXT
            output_path = input_path.with_name(f"{input_path.stem}.digest{input_path.suffix}")

        # Check if output exists
        if output_path.exists() and not force and not dry_run:
            overwrite = typer.confirm(f"Output file {output_path} already exists. Overwrite?")
            if not overwrite:
                print_info("Operation cancelled")
                sys.exit(ExitCode.SUCCESS)

        # Write digest (unless dry run)
        if dry_run:
            print_info("DRY RUN - No files will be written\n")
            print_info(f"Would write digest to: {output_path}")
            print_info(f"Original: {spec.token_count:,} tokens")
            print_info(f"Digest:   {digest_obj.token_count:,} tokens")
            savings = digest_obj.calculate_savings()
            ratio = digest_obj.compression_ratio
            print_info(f"Saved:    {savings:,} tokens ({ratio:.1%})")
        else:
            digest_obj.to_file(output_path)

            # Success message
            print_success("Digest generated successfully\n")
            console.print(f"Input:  [path]{input_path}[/path] ({spec.token_count:,} tokens)")
            console.print(f"Output: [path]{output_path}[/path] ({digest_obj.token_count:,} tokens)")
            savings = digest_obj.calculate_savings()
            ratio = digest_obj.compression_ratio
            console.print(f"Saved:  [metric]{savings:,} tokens ({ratio:.1%})[/metric]\n")
            console.print(f"Time:   {metrics.processing_time_ms}ms")
            console.print(f"Format: {spec.format.value} → {digest_obj.format.value}")
            console.print(f"Profile: {compression_level.value} compression")

            metrics.digest_file = str(output_path)

            # Show metrics if requested
            if show_metrics:
                console.print()
                metrics.display()

        sys.exit(ExitCode.SUCCESS)

    except FileNotFoundError as e:
        print_error("File Not Found", str(e), "Check the file path and try again")
        sys.exit(ExitCode.GENERAL_ERROR)

    except ValueError as e:
        print_error("Validation Error", str(e))
        sys.exit(ExitCode.VALIDATION_ERROR)

    except PermissionError as e:
        print_error("Permission Denied", str(e), "Check file permissions")
        sys.exit(ExitCode.IO_ERROR)

    except Exception as e:
        print_error("Unexpected Error", str(e))
        if _debug:
            console.print_exception()
        sys.exit(ExitCode.GENERAL_ERROR)


@app.command()
def metrics(
    digest_file: str = typer.Argument(..., help="Path to digest file"),
    output_format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format (table/json/yaml)",
    ),
    breakdown: bool = typer.Option(
        False,
        "--breakdown",
        "-b",
        help="Show per-section breakdown",
    ),
):
    """Display token savings metrics for a generated digest.

    Examples:

        # Basic metrics display
        specnut metrics spec.digest.md

        # JSON output
        specnut metrics spec.digest.md -f json

        # Show section breakdown
        specnut metrics spec.digest.md --breakdown
    """
    from pathlib import Path

    from specnut.cli.styles import print_error, print_success
    from specnut.models.digest import Digest

    try:
        # Validate input file
        digest_path = Path(digest_file)
        if not digest_path.exists():
            print_error(
                "File Not Found",
                f"{digest_file} does not exist",
                "Check the file path and try again",
            )
            sys.exit(ExitCode.GENERAL_ERROR)

        if not digest_path.is_file():
            print_error(
                "Invalid Input",
                f"{digest_file} is not a file",
                "Provide a path to a digest file",
            )
            sys.exit(ExitCode.GENERAL_ERROR)

        # Load digest
        if _verbose or _debug:
            from specnut.cli.styles import print_info

            print_info(f"Loading digest from: {digest_path}")

        digest = Digest.from_file(digest_path)

        # Create metrics from digest metadata
        from specnut.models.metrics import TokenMetrics

        # Extract source file from metadata if available
        source_file = (
            str(digest.source_spec.file_path)
            if digest.source_spec
            else digest.metadata.source_hash[:16]
        )

        metrics_obj = TokenMetrics(
            original_tokens=digest.source_spec.token_count if digest.source_spec else 0,
            digest_tokens=digest.token_count,
            percent_saved=digest.compression_ratio,
            processing_time_ms=0,  # Not available from saved digest
            timestamp=digest.metadata.timestamp,
            source_file=source_file,
            digest_file=str(digest_path),
            sections_breakdown={},  # Will be populated if available
        )

        # Display metrics based on format
        if output_format == "json":
            console.print(metrics_obj.to_json())
        elif output_format == "yaml":
            import yaml

            console.print(yaml.dump(json.loads(metrics_obj.to_json()), default_flow_style=False))
        elif output_format == "table":
            # Display summary
            print_success(f"Metrics for: {digest_path.name}\n")
            console.print(f"Source:     [path]{source_file}[/path]")
            console.print(f"Digest:     [path]{digest_path}[/path]")
            console.print(f"Profile:    {digest.metadata.optimization_profile}")
            console.print(f"Format:     {digest.format.value}")
            console.print()

            # Display token metrics
            console.print(f"Original:   {metrics_obj.original_tokens:,} tokens")
            console.print(f"Digest:     {metrics_obj.digest_tokens:,} tokens")
            savings = digest.calculate_savings()
            ratio = digest.compression_ratio
            console.print(f"[metric]Saved:      {savings:,} tokens ({ratio:.1%})[/metric]")
            console.print()

            # Display section breakdown if requested
            if breakdown:
                console.print(
                    "[yellow]⚠ Section breakdown not available from saved digest[/yellow]"
                )
                console.print(
                    "Section metrics are only available during generation with --show-metrics"
                )
        else:
            print_error(
                "Invalid Format",
                f"Format '{output_format}' is not supported",
                "Use one of: table, json, yaml",
            )
            sys.exit(ExitCode.VALIDATION_ERROR)

        sys.exit(ExitCode.SUCCESS)

    except FileNotFoundError as e:
        print_error("File Not Found", str(e), "Check the file path and try again")
        sys.exit(ExitCode.GENERAL_ERROR)

    except ValueError as e:
        print_error("Invalid Digest", str(e), "The file may not be a valid digest")
        sys.exit(ExitCode.VALIDATION_ERROR)

    except Exception as e:
        print_error("Unexpected Error", str(e))
        if _debug:
            console.print_exception()
        sys.exit(ExitCode.GENERAL_ERROR)


if __name__ == "__main__":
    app()
