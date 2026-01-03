"""TokenMetrics model for tracking optimization statistics."""

import json
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SectionMetrics:
    """Per-section token statistics.

    Attributes:
        section_name: Name of the section (e.g., "User Stories")
        original_tokens: Tokens before compression
        digest_tokens: Tokens after compression
        reduction_percent: Percentage saved for this section
        action_taken: What was done (preserved/summarized/compressed/omitted)
    """

    section_name: str
    original_tokens: int
    digest_tokens: int
    reduction_percent: float
    action_taken: str


@dataclass
class TokenMetrics:
    """Statistics and analytics about the optimization process.

    Attributes:
        original_tokens: Token count of source specification
        digest_tokens: Token count of generated digest
        percent_saved: Percentage reduction (0.0 to 1.0)
        processing_time_ms: Time taken to generate digest (milliseconds)
        timestamp: When metrics were captured
        source_file: Path to source file (for reference)
        digest_file: Path to digest file (if saved)
        sections_breakdown: Per-section token statistics
    """

    original_tokens: int
    digest_tokens: int
    percent_saved: float
    processing_time_ms: int
    timestamp: datetime
    source_file: str
    digest_file: str = ""
    sections_breakdown: dict[str, SectionMetrics] = field(default_factory=dict)

    def __post_init__(self):
        """Validate metrics after initialization."""
        if self.original_tokens <= 0:
            raise ValueError(f"Original tokens must be positive, got {self.original_tokens}")

        if self.digest_tokens <= 0:
            raise ValueError(f"Digest tokens must be positive, got {self.digest_tokens}")

        if self.digest_tokens >= self.original_tokens:
            raise ValueError(
                f"Digest tokens ({self.digest_tokens}) must be less than "
                f"original tokens ({self.original_tokens})"
            )

        if self.percent_saved < 0.0 or self.percent_saved > 1.0:
            raise ValueError(f"Percent saved must be between 0.0 and 1.0, got {self.percent_saved}")

        if self.processing_time_ms < 0:
            raise ValueError(f"Processing time must be non-negative, got {self.processing_time_ms}")

    def display(self) -> None:
        """Pretty-print metrics using Rich tables.

        This will be implemented when Rich is available in the CLI layer.
        For now, we'll use a simple print.
        """
        try:
            from rich.console import Console
            from rich.table import Table

            console = Console()

            # Main metrics table
            table = Table(title="Token Optimization Metrics", show_header=False)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Source", self.source_file)
            if self.digest_file:
                table.add_row("Digest", self.digest_file)
            table.add_row("Generated", self.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            table.add_row("", "")
            table.add_row("Original", f"{self.original_tokens:,} tokens")
            table.add_row("Optimized", f"{self.digest_tokens:,} tokens")
            table.add_row(
                "Saved",
                f"{self.original_tokens - self.digest_tokens:,} tokens ({self.percent_saved:.1%})",
            )
            table.add_row("", "")
            table.add_row("Processing", f"{self.processing_time_ms}ms")

            console.print(table)

            # Section breakdown if available
            if self.sections_breakdown:
                breakdown_table = Table(title="Section Breakdown")
                breakdown_table.add_column("Section", style="cyan")
                breakdown_table.add_column("Original", justify="right")
                breakdown_table.add_column("Digest", justify="right")
                breakdown_table.add_column("Saved", justify="right")
                breakdown_table.add_column("Action")

                for section_name, metrics in self.sections_breakdown.items():
                    breakdown_table.add_row(
                        section_name,
                        f"{metrics.original_tokens:,}",
                        f"{metrics.digest_tokens:,}",
                        f"{metrics.reduction_percent:.1%}",
                        metrics.action_taken,
                    )

                console.print(breakdown_table)

        except ImportError:
            # Fallback if Rich is not available
            print("\nToken Optimization Metrics")
            print("=" * 50)
            print(f"Source:     {self.source_file}")
            if self.digest_file:
                print(f"Digest:     {self.digest_file}")
            print(f"Generated:  {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"\nOriginal:   {self.original_tokens:,} tokens")
            print(f"Optimized:  {self.digest_tokens:,} tokens")
            saved = self.original_tokens - self.digest_tokens
            print(f"Saved:      {saved:,} tokens ({self.percent_saved:.1%})")
            print(f"\nProcessing: {self.processing_time_ms}ms")

    def to_json(self) -> str:
        """Serialize to JSON for logging/export.

        Returns:
            JSON string representation
        """
        data = {
            "source_file": self.source_file,
            "digest_file": self.digest_file,
            "timestamp": self.timestamp.isoformat(),
            "original_tokens": self.original_tokens,
            "digest_tokens": self.digest_tokens,
            "tokens_saved": self.original_tokens - self.digest_tokens,
            "percent_saved": self.percent_saved,
            "processing_time_ms": self.processing_time_ms,
            "section_breakdown": [
                {
                    "section": name,
                    "original_tokens": metrics.original_tokens,
                    "digest_tokens": metrics.digest_tokens,
                    "reduction_percent": metrics.reduction_percent,
                    "action": metrics.action_taken,
                }
                for name, metrics in self.sections_breakdown.items()
            ],
        }
        return json.dumps(data, indent=2)

    def validate_performance(self) -> bool:
        """Check if meets SC-003 (<10s for files up to 50,000 tokens).

        Returns:
            True if performance is acceptable, False otherwise
        """
        # For files up to 50,000 tokens, should complete in <10 seconds
        if self.original_tokens <= 50_000:
            return self.processing_time_ms < 10_000
        return True  # No strict requirement for larger files
