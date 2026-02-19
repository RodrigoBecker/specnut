"""
Unit tests for batch processing data models.
Tests ProcessingStatus, FileProcessingResult, ProcessingSummary, DirectoryScanResult.
"""

import pytest
from pathlib import Path
from specnut.models.metrics import (
    ProcessingStatus,
    FileProcessingResult,
    ProcessingSummary,
    DirectoryScanResult,
)


class TestProcessingStatus:
    """Test ProcessingStatus enum."""

    def test_enum_has_expected_values(self):
        """Enum defines success, failed, and skipped statuses."""
        assert ProcessingStatus.SUCCESS.value == "success"
        assert ProcessingStatus.FAILED.value == "failed"
        assert ProcessingStatus.SKIPPED.value == "skipped"

    def test_enum_values_are_strings(self):
        """All enum values are strings."""
        assert isinstance(ProcessingStatus.SUCCESS.value, str)
        assert isinstance(ProcessingStatus.FAILED.value, str)
        assert isinstance(ProcessingStatus.SKIPPED.value, str)

    def test_enum_has_exactly_three_values(self):
        """Enum has exactly 3 status values."""
        assert len(ProcessingStatus) == 3


class TestFileProcessingResult:
    """Test FileProcessingResult dataclass."""

    def test_create_success_factory_method(self):
        """create_success() creates successful result."""
        result = FileProcessingResult.create_success(
            file_path=Path("test.md"),
            original_tokens=1000,
            digest_tokens=650,
            output_path=Path("test.digest.md"),
            processing_time_ms=500
        )

        assert result.status == ProcessingStatus.SUCCESS
        assert result.file_path == Path("test.md")
        assert result.original_tokens == 1000
        assert result.digest_tokens == 650
        assert result.compression_ratio == 0.35  # (1000-650)/1000
        assert result.error_message is None

    def test_create_failure_factory_method(self):
        """create_failure() creates failed result from exception."""
        error = ValueError("Invalid YAML syntax")
        result = FileProcessingResult.create_failure(
            file_path=Path("broken.yaml"),
            error=error
        )

        assert result.status == ProcessingStatus.FAILED
        assert result.file_path == Path("broken.yaml")
        assert result.error_type == "ValueError"
        assert result.error_message == "Invalid YAML syntax"
        assert result.original_tokens == 0
        assert result.digest_tokens == 0

    def test_is_successful_method(self):
        """is_successful() returns True only for successful results."""
        success = FileProcessingResult.create_success(
            Path("test.md"), 100, 65, Path("test.digest.md"), 100
        )
        failure = FileProcessingResult.create_failure(
            Path("broken.yaml"), ValueError("Error")
        )

        assert success.is_successful() is True
        assert failure.is_successful() is False

    def test_compression_ratio_calculation(self):
        """Compression ratio calculated correctly."""
        result = FileProcessingResult.create_success(
            Path("test.md"), 10000, 6500, Path("test.digest.md"), 100
        )
        assert result.compression_ratio == 0.35


class TestProcessingSummary:
    """Test ProcessingSummary aggregate model."""

    def test_from_results_aggregates_metrics(self):
        """from_results() correctly aggregates file results."""
        results = [
            FileProcessingResult.create_success(
                Path("file1.md"), 1000, 650, Path("file1.digest.md"), 100
            ),
            FileProcessingResult.create_success(
                Path("file2.md"), 2000, 1400, Path("file2.digest.md"), 200
            ),
            FileProcessingResult.create_failure(
                Path("broken.yaml"), ValueError("Error")
            ),
        ]

        summary = ProcessingSummary.from_results(results)

        assert summary.total_files == 3
        assert summary.successful_count == 2
        assert summary.failed_count == 1
        assert summary.skipped_count == 0
        assert summary.total_original_tokens == 3000
        assert summary.total_digest_tokens == 2050
        assert summary.total_tokens_saved == 950

    def test_average_compression_ratio_weighted(self):
        """Average compression ratio is weighted by token count."""
        results = [
            FileProcessingResult.create_success(
                Path("large.md"), 10000, 6500, Path("large.digest.md"), 100
            ),  # 35% compression
            FileProcessingResult.create_success(
                Path("small.md"), 1000, 700, Path("small.digest.md"), 50
            ),  # 30% compression
        ]

        summary = ProcessingSummary.from_results(results)

        # Weighted: (3500 + 300) / 11000 = 0.345...
        assert abs(summary.average_compression_ratio - 0.345) < 0.001

    def test_get_failed_files(self):
        """get_failed_files() returns only failed results."""
        results = [
            FileProcessingResult.create_success(
                Path("ok.md"), 100, 65, Path("ok.digest.md"), 50
            ),
            FileProcessingResult.create_failure(
                Path("bad.yaml"), ValueError("Error")
            ),
        ]

        summary = ProcessingSummary.from_results(results)
        failed = summary.get_failed_files()

        assert len(failed) == 1
        assert failed[0].file_path == Path("bad.yaml")

    def test_get_successful_files(self):
        """get_successful_files() returns only successful results."""
        results = [
            FileProcessingResult.create_success(
                Path("ok.md"), 100, 65, Path("ok.digest.md"), 50
            ),
            FileProcessingResult.create_failure(
                Path("bad.yaml"), ValueError("Error")
            ),
        ]

        summary = ProcessingSummary.from_results(results)
        successful = summary.get_successful_files()

        assert len(successful) == 1
        assert successful[0].file_path == Path("ok.md")

    def test_success_rate_property(self):
        """success_rate property calculates percentage correctly."""
        results = [
            FileProcessingResult.create_success(
                Path("ok1.md"), 100, 65, Path("ok1.digest.md"), 50
            ),
            FileProcessingResult.create_success(
                Path("ok2.md"), 100, 65, Path("ok2.digest.md"), 50
            ),
            FileProcessingResult.create_failure(
                Path("bad.yaml"), ValueError("Error")
            ),
        ]

        summary = ProcessingSummary.from_results(results)
        assert abs(summary.success_rate - 0.666) < 0.01  # 2/3

    def test_has_failures_property(self):
        """has_failures property returns True when failures exist."""
        all_success = ProcessingSummary.from_results([
            FileProcessingResult.create_success(
                Path("ok.md"), 100, 65, Path("ok.digest.md"), 50
            )
        ])
        with_failures = ProcessingSummary.from_results([
            FileProcessingResult.create_success(
                Path("ok.md"), 100, 65, Path("ok.digest.md"), 50
            ),
            FileProcessingResult.create_failure(
                Path("bad.yaml"), ValueError("Error")
            ),
        ])

        assert all_success.has_failures is False
        assert with_failures.has_failures is True


class TestDirectoryScanResult:
    """Test DirectoryScanResult model."""

    def test_validate_raises_on_empty_files(self):
        """validate() raises ValueError if no files found."""
        scan = DirectoryScanResult(
            input_path=Path("/tmp/empty"),
            files_found=[],
            total_count=0,
            patterns_used=["*.md"],
            recursive=True
        )

        with pytest.raises(ValueError, match="No files found"):
            scan.validate()

    def test_validate_passes_with_files(self):
        """validate() succeeds when files found."""
        scan = DirectoryScanResult(
            input_path=Path("/tmp/specs"),
            files_found=[Path("spec.md")],
            total_count=1,
            patterns_used=["*.md"],
            recursive=True
        )

        scan.validate()  # Should not raise

    def test_filter_by_extension(self):
        """filter_by_extension() filters files correctly."""
        scan = DirectoryScanResult(
            input_path=Path("/tmp"),
            files_found=[
                Path("file1.md"),
                Path("file2.yaml"),
                Path("file3.json"),
                Path("file4.md"),
            ],
            total_count=4,
            patterns_used=["*.md", "*.yaml", "*.json"],
            recursive=True
        )

        md_files = scan.filter_by_extension([".md"])
        assert len(md_files) == 2
        assert all(f.suffix == ".md" for f in md_files)

    def test_from_directory_class_method(self, tmp_path):
        """from_directory() scans and creates result object."""
        # Create test files
        (tmp_path / "spec1.md").write_text("# Spec 1")
        (tmp_path / "spec2.yaml").write_text("title: Spec 2")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "spec3.md").write_text("# Spec 3")

        scan = DirectoryScanResult.from_directory(
            path=tmp_path,
            patterns=["*.md", "*.yaml"],
            recursive=True
        )

        assert scan.input_path == tmp_path
        assert scan.total_count == 3
        assert scan.recursive is True
        assert "*.md" in scan.patterns_used
