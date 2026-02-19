"""TokenMetrics model for tracking optimization statistics."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


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


# ============================================================================
# Batch Processing Models (Feature: 002-directory-digest)
# ============================================================================


class ProcessingStatus(str, Enum):
    """Status of file processing operation in batch mode."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FileProcessingResult:
    """Result of processing a single file in batch mode.

    Attributes:
        file_path: Path to the file processed
        status: Success/failed/skipped status
        original_tokens: Token count before optimization
        digest_tokens: Token count after optimization
        processing_time_ms: Time taken to process file
        output_path: Path to generated digest file (if successful)
        error_type: Type of error that occurred (if failed)
        error_message: Detailed error message (if failed)
        compression_ratio: Percentage saved (0.0-1.0)
    """

    file_path: Path
    status: ProcessingStatus
    original_tokens: int
    digest_tokens: int
    processing_time_ms: int = 0
    output_path: Path | None = None
    error_type: str | None = None
    error_message: str | None = None
    compression_ratio: float = field(init=False)

    def __post_init__(self):
        """Calculate compression ratio after initialization."""
        if self.status == ProcessingStatus.SUCCESS and self.original_tokens > 0:
            self.compression_ratio = (
                self.original_tokens - self.digest_tokens
            ) / self.original_tokens
        else:
            self.compression_ratio = 0.0

    @classmethod
    def create_success(
        cls,
        file_path: Path,
        original_tokens: int,
        digest_tokens: int,
        output_path: Path,
        processing_time_ms: int,
    ) -> "FileProcessingResult":
        """Create successful processing result.

        Args:
            file_path: Path to source file
            original_tokens: Token count before optimization
            digest_tokens: Token count after optimization
            output_path: Path to generated digest file
            processing_time_ms: Processing time in milliseconds

        Returns:
            FileProcessingResult with SUCCESS status
        """
        return cls(
            file_path=file_path,
            status=ProcessingStatus.SUCCESS,
            original_tokens=original_tokens,
            digest_tokens=digest_tokens,
            processing_time_ms=processing_time_ms,
            output_path=output_path,
        )

    @classmethod
    def create_failure(
        cls, file_path: Path, error: Exception
    ) -> "FileProcessingResult":
        """Create failed processing result from exception.

        Args:
            file_path: Path to file that failed
            error: Exception that occurred

        Returns:
            FileProcessingResult with FAILED status
        """
        return cls(
            file_path=file_path,
            status=ProcessingStatus.FAILED,
            original_tokens=0,
            digest_tokens=0,
            error_type=type(error).__name__,
            error_message=str(error),
        )

    def is_successful(self) -> bool:
        """Check if processing was successful.

        Returns:
            True if status is SUCCESS, False otherwise
        """
        return self.status == ProcessingStatus.SUCCESS


@dataclass
class ProcessingSummary:
    """Aggregate summary of batch processing results.

    Attributes:
        total_files: Total number of files attempted
        successful_count: Number of successful files
        failed_count: Number of failed files
        skipped_count: Number of skipped files
        results: Individual file results
        total_original_tokens: Sum of original tokens (successful files only)
        total_digest_tokens: Sum of digest tokens (successful files only)
        total_tokens_saved: Total tokens saved
        average_compression_ratio: Weighted average compression
        total_processing_time_ms: Sum of processing times
        timestamp: When summary was generated
    """

    total_files: int
    successful_count: int
    failed_count: int
    skipped_count: int
    results: list[FileProcessingResult]
    total_original_tokens: int
    total_digest_tokens: int
    total_tokens_saved: int
    average_compression_ratio: float
    total_processing_time_ms: int
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_results(
        cls, results: list[FileProcessingResult]
    ) -> "ProcessingSummary":
        """Create summary from list of file results.

        Args:
            results: List of file processing results

        Returns:
            ProcessingSummary with aggregated metrics
        """
        total_files = len(results)
        successful = [r for r in results if r.status == ProcessingStatus.SUCCESS]
        failed = [r for r in results if r.status == ProcessingStatus.FAILED]
        skipped = [r for r in results if r.status == ProcessingStatus.SKIPPED]

        # Aggregate token counts (only from successful files)
        total_original = sum(r.original_tokens for r in successful)
        total_digest = sum(r.digest_tokens for r in successful)
        total_saved = total_original - total_digest

        # Calculate weighted average compression ratio
        if total_original > 0:
            avg_compression = total_saved / total_original
        else:
            avg_compression = 0.0

        # Sum processing times
        total_time = sum(r.processing_time_ms for r in results)

        return cls(
            total_files=total_files,
            successful_count=len(successful),
            failed_count=len(failed),
            skipped_count=len(skipped),
            results=results,
            total_original_tokens=total_original,
            total_digest_tokens=total_digest,
            total_tokens_saved=total_saved,
            average_compression_ratio=avg_compression,
            total_processing_time_ms=total_time,
        )

    def get_failed_files(self) -> list[FileProcessingResult]:
        """Return only failed file results.

        Returns:
            List of FileProcessingResult with FAILED status
        """
        return [r for r in self.results if r.status == ProcessingStatus.FAILED]

    def get_successful_files(self) -> list[FileProcessingResult]:
        """Return only successful file results.

        Returns:
            List of FileProcessingResult with SUCCESS status
        """
        return [r for r in self.results if r.status == ProcessingStatus.SUCCESS]

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage.

        Returns:
            Success rate (0.0 to 1.0)
        """
        if self.total_files == 0:
            return 0.0
        return self.successful_count / self.total_files

    @property
    def has_failures(self) -> bool:
        """Check if any files failed.

        Returns:
            True if failed_count > 0, False otherwise
        """
        return self.failed_count > 0


@dataclass
class DirectoryScanResult:
    """Results of scanning a directory for specification files.

    Attributes:
        input_path: Directory that was scanned
        files_found: List of discovered specification files
        total_count: Total number of files discovered
        patterns_used: Glob patterns used for matching
        recursive: Whether subdirectories were scanned
        max_depth: Maximum directory depth scanned (optional)
    """

    input_path: Path
    files_found: list[Path]
    total_count: int
    patterns_used: list[str]
    recursive: bool
    max_depth: int | None = None

    def validate(self) -> None:
        """Validate that at least one file was found.

        Raises:
            ValueError: If no files found matching patterns
        """
        if self.total_count == 0 or len(self.files_found) == 0:
            raise ValueError(
                f"No files found in {self.input_path} matching patterns {self.patterns_used}"
            )

    def filter_by_extension(self, extensions: list[str]) -> list[Path]:
        """Filter files by specific extensions.

        Args:
            extensions: List of extensions to filter (e.g., [".md", ".yaml"])

        Returns:
            List of Path objects matching the extensions
        """
        return [f for f in self.files_found if f.suffix in extensions]

    @classmethod
    def from_directory(
        cls, path: Path, patterns: list[str], recursive: bool
    ) -> "DirectoryScanResult":
        """Scan directory and create result object.

        Args:
            path: Directory to scan
            patterns: Glob patterns to match (e.g., ["*.md", "*.yaml"])
            recursive: Whether to scan subdirectories

        Returns:
            DirectoryScanResult with discovered files
        """
        files = []

        for pattern in patterns:
            if recursive:
                files.extend(path.rglob(pattern))
            else:
                files.extend(path.glob(pattern))

        # Remove duplicates and sort for deterministic ordering
        files = sorted(set(files))

        return cls(
            input_path=path,
            files_found=files,
            total_count=len(files),
            patterns_used=patterns,
            recursive=recursive,
        )
