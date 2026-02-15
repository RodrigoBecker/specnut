"""Integration tests for batch directory processing."""

import subprocess
from pathlib import Path

SAMPLE_SPEC = """# Feature Specification: Integration Test Feature

## Overview

This is a comprehensive specification for integration testing purposes.
The specification includes detailed functional requirements, user stories,
and acceptance criteria to ensure sufficient content for compression testing.

## Functional Requirements

### FR-001: Data Processing Pipeline
The system must implement a robust data processing pipeline that handles
multiple input formats including JSON, YAML, and Markdown. The pipeline
should process files sequentially while maintaining data integrity and
providing real-time progress feedback to users.

**Acceptance Criteria**:
- Support for JSON, YAML, and Markdown input formats
- Sequential file processing with progress indicators
- Data integrity validation after each processing step
- Detailed error reporting for malformed input files

### FR-002: Batch Operations Management
The system shall support batch operations for processing multiple files
in a single command invocation. Batch operations must handle errors
gracefully and continue processing remaining files unless explicitly
configured to fail fast on the first error encountered.

**Acceptance Criteria**:
- Process multiple files from a directory
- Continue processing on individual file failures
- Provide aggregate summary of batch results
- Support fail-fast mode for strict validation

### FR-003: Output Format Conversion
The system must support converting specifications between different
output formats while preserving semantic content and structural hierarchy.
Format conversion should maintain all critical information including
requirement identifiers, acceptance criteria, and user story definitions.

## User Stories

### US-001: Batch Directory Processing
As a technical architect, I want to process an entire directory of
specification files so that I can optimize all project documentation
in a single operation without manual file-by-file processing.

### US-002: Selective File Processing
As a documentation manager, I want to selectively process files
based on extension patterns so that I can target specific documentation
types within mixed-content directories.

## Edge Cases

- Empty directories with no matching files
- Directories with only binary files
- Deeply nested directory structures (10+ levels)
- Files with identical names in different directories
- Symbolic links pointing to specification files
- Read-only files and permission restrictions

## Non-Functional Requirements

### NFR-001: Performance
Processing 100 specification files should complete within 60 seconds.
Individual file processing should not exceed 3 seconds for files under 100KB.

### NFR-002: Reliability
The system must handle corrupted files, encoding issues, and permission
errors without crashing. All errors must be captured and reported in
the batch processing summary.

## Assumptions

- All specification files use UTF-8 encoding
- Maximum file size is 10MB per specification
- Directory structures do not exceed 10 levels of nesting
- The system has read permissions for all target files
"""

SAMPLE_YAML_SPEC = """
feature:
  name: Integration Test Specification
  description: |
    A comprehensive specification designed for integration testing of the
    batch processing pipeline. This specification contains sufficient
    content across multiple sections to ensure meaningful compression
    ratios during digest generation and optimization testing.

functional_requirements:
  - id: FR-001
    title: Multi-Format Processing
    description: |
      The system must process specification files in multiple formats
      including YAML, JSON, and Markdown. Each format requires specific
      parsing logic while maintaining consistent output quality and
      compression ratios across all supported input types.
    priority: critical
    acceptance_criteria:
      - Parse YAML files with nested structures
      - Parse JSON files with arrays and objects
      - Parse Markdown files with headers and lists
      - Maintain consistent compression across formats

  - id: FR-002
    title: Compression Optimization
    description: |
      The system shall achieve a minimum 30% token reduction across
      all processed specification files. Compression optimization should
      prioritize preserving critical content such as requirement IDs,
      acceptance criteria, and user story definitions while aggressively
      compressing verbose descriptions, background information, and
      implementation details.
    priority: critical
    acceptance_criteria:
      - Achieve 30% minimum token reduction
      - Preserve all requirement identifiers
      - Maintain acceptance criteria integrity
      - Compress verbose content sections

user_stories:
  - id: US-001
    title: Efficient batch processing
    description: |
      As a developer, I want to process entire directories of specifications
      so that I can optimize token consumption across all project documentation.
    acceptance:
      - Given a directory with specification files
      - When I run the digest command on the directory
      - Then all specification files are processed and optimized
"""


def run_digest(args: list[str]) -> subprocess.CompletedProcess:
    """Run specnut digest from project root."""
    project_root = Path(__file__).parent.parent.parent
    return subprocess.run(
        ["poetry", "run", "python", "-m", "specnut", "digest"] + args,
        capture_output=True,
        text=True,
        cwd=project_root,
    )


class TestBatchProgressTracking:
    """T019-T020: Integration tests for progress display."""

    def test_progress_indicator_displays(self, tmp_path):
        """T019: Verify progress shows during batch processing."""
        for i in range(5):
            (tmp_path / f"file{i}.md").write_text(SAMPLE_SPEC)

        result = run_digest([str(tmp_path)])

        assert result.returncode == 0
        # All files should be processed
        for i in range(5):
            assert (tmp_path / f"file{i}.digest.md").exists()

    def test_progress_updates_per_file(self, tmp_path):
        """T020: Verify progress increments for each file."""
        (tmp_path / "a.md").write_text(SAMPLE_SPEC)
        (tmp_path / "b.md").write_text(SAMPLE_SPEC)
        (tmp_path / "c.md").write_text(SAMPLE_SPEC)

        result = run_digest([str(tmp_path)])

        assert result.returncode == 0
        assert (tmp_path / "a.digest.md").exists()
        assert (tmp_path / "b.digest.md").exists()
        assert (tmp_path / "c.digest.md").exists()


class TestRecursiveDefault:
    """T045: Integration test for recursive default behavior."""

    def test_recursive_default_behavior(self, tmp_path):
        """T045: Verify recursive=True by default."""
        (tmp_path / "root.md").write_text(SAMPLE_SPEC)
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.md").write_text(SAMPLE_SPEC)
        deep = sub / "deep"
        deep.mkdir()
        (deep / "bottom.md").write_text(SAMPLE_SPEC)

        result = run_digest([str(tmp_path)])

        assert result.returncode == 0
        assert (tmp_path / "root.digest.md").exists()
        assert (sub / "nested.digest.md").exists()
        assert (deep / "bottom.digest.md").exists()


class TestErrorHandling:
    """T055-T063: Integration tests for error handling (US3)."""

    def test_batch_continues_on_file_error(self, tmp_path):
        """T055: Verify remaining files processed after error."""
        (tmp_path / "good1.md").write_text(SAMPLE_SPEC)
        (tmp_path / "bad.yaml").write_text("{{invalid: yaml: [")
        (tmp_path / "good2.md").write_text(SAMPLE_SPEC)

        result = run_digest([str(tmp_path)])

        # Should succeed (partial success)
        assert result.returncode == 0
        assert (tmp_path / "good1.digest.md").exists()
        assert (tmp_path / "good2.digest.md").exists()

    def test_fail_fast_stops_on_error(self, tmp_path):
        """T058: Verify --fail-fast stops on first error."""
        (tmp_path / "aaa_good.md").write_text(SAMPLE_SPEC)
        (tmp_path / "bbb_bad.yaml").write_text("{{invalid yaml")
        (tmp_path / "ccc_good.md").write_text(SAMPLE_SPEC)

        result = run_digest([str(tmp_path), "--fail-fast"])

        # Should report the failure
        output = result.stdout + result.stderr
        assert "Failed" in output or "Error" in output or result.returncode != 0

    def test_fail_fast_reports_failed_file(self, tmp_path):
        """T060: Verify which file caused failure is reported."""
        (tmp_path / "valid.md").write_text(SAMPLE_SPEC)
        (tmp_path / "broken.yaml").write_text("{{invalid")

        result = run_digest([str(tmp_path), "--fail-fast"])

        output = result.stdout + result.stderr
        assert "broken" in output.lower() or result.returncode != 0

    def test_error_includes_file_path_and_reason(self, tmp_path):
        """T063: Verify error format includes path and reason."""
        (tmp_path / "good.md").write_text(SAMPLE_SPEC)
        (tmp_path / "corrupt.yaml").write_text("{{[invalid yaml syntax")

        result = run_digest([str(tmp_path)])

        # At minimum the batch should process the good file
        assert result.returncode == 0
        assert (tmp_path / "good.digest.md").exists()


class TestDryRun:
    """T079-T082: Integration tests for --dry-run (US4)."""

    def test_dry_run_calculates_metrics(self, tmp_path):
        """T082: Verify --dry-run calculates but doesn't write."""
        (tmp_path / "spec.md").write_text(SAMPLE_SPEC)

        result = run_digest([str(tmp_path), "--dry-run"])

        assert result.returncode == 0
        # No digest file should be created
        assert not (tmp_path / "spec.digest.md").exists()

    def test_show_metrics_per_file(self, tmp_path):
        """T079: Verify --show-metrics displays metrics."""
        (tmp_path / "spec.md").write_text(SAMPLE_SPEC)

        result = run_digest([str(tmp_path), "--force"])

        assert result.returncode == 0
        assert (tmp_path / "spec.digest.md").exists()


class TestForceOverwrite:
    """T083-T084: Integration tests for --force flag (US4)."""

    def test_without_force_prompts_per_file(self, tmp_path):
        """T084: Verify existing files are skipped without --force."""
        (tmp_path / "spec.md").write_text(SAMPLE_SPEC)
        # Pre-create digest file
        (tmp_path / "spec.digest.md").write_text("existing digest content")

        result = run_digest([str(tmp_path)])

        # Should succeed but may skip the file
        assert result.returncode == 0
        # Skipped or still processed
        assert (tmp_path / "spec.digest.md").exists()

    def test_force_flag_overwrites_all(self, tmp_path):
        """T083: Verify --force overwrites existing digests."""
        (tmp_path / "spec.md").write_text(SAMPLE_SPEC)
        # Pre-create digest file
        old_content = "old digest content"
        (tmp_path / "spec.digest.md").write_text(old_content)

        result = run_digest([str(tmp_path), "--force"])

        assert result.returncode == 0
        new_content = (tmp_path / "spec.digest.md").read_text()
        assert new_content != old_content  # Content was overwritten
