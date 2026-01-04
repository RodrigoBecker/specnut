"""
Contract tests for batch processing command-line options.
Tests for --include and --no-recursive flags (User Story 2).
"""

import subprocess
from pathlib import Path

import pytest

# Sample test data - expanded to ensure good compression
SAMPLE_SPEC = """# Test Specification: Advanced Feature Processing System

## Overview
This is a comprehensive test specification file with substantial content designed
to compress properly during digest processing. It includes multiple detailed sections,
extensive descriptions, and thorough documentation to ensure the token count is
sufficiently high for meaningful compression testing across all supported file formats.

## Functional Requirements

### FR-001: Core Processing Capabilities
The system must provide robust processing capabilities for handling various specification
formats including Markdown, YAML, JSON, and custom text-based formats. All processing
operations should be optimized for performance and maintain data integrity throughout
the transformation pipeline.

**Acceptance Criteria**:
- Support for all standard specification formats (.md, .yaml, .yml, .json)
- Successful parsing of nested data structures and complex hierarchies
- Validation of input data against predefined schemas and rules
- Error recovery mechanisms for malformed or corrupted input files

### FR-002: Batch Processing Operations
Implement comprehensive batch processing functionality that enables users to process
multiple specification files simultaneously. The system should handle large volumes
of files efficiently while providing detailed progress tracking and error reporting.

**Acceptance Criteria**:
- Process directories containing hundreds of specification files
- Recursive directory traversal with configurable depth limits
- Real-time progress indicators showing current file and completion percentage
- Detailed summary reports with token metrics and compression statistics

### FR-003: Custom Extension Support
Enable users to process specification files with custom file extensions beyond the
standard supported formats. The system should intelligently detect content format
and apply appropriate parsing strategies based on file content patterns.

**Acceptance Criteria**:
- Support for user-defined file patterns via --include flag
- Automatic format detection for custom extensions
- Fallback to markdown parsing for unknown text-based formats
- Clear error messages for binary or unsupported file types

## User Stories

### US-001: Efficient Specification Processing
As a technical writer, I want to process large specification documents efficiently
so that I can reduce token consumption when working with AI-assisted documentation
tools and maintain cost-effective workflows for large-scale documentation projects.

### US-002: Batch Documentation Updates
As a documentation manager, I want to process entire directories of specifications
in a single operation so that I can streamline my workflow and ensure consistent
processing across all project documentation artifacts.

## Non-Functional Requirements

### NFR-001: Performance
All processing operations must complete within reasonable time constraints to ensure
user productivity. Single file processing should complete in under 3 seconds for
files up to 100KB. Batch processing should handle at least 100 files per minute.

### NFR-002: Reliability
The system must handle errors gracefully and continue processing remaining files
when individual files fail. Failed files should be clearly reported with specific
error details to facilitate debugging and resolution.
"""


def run_digest(args: list[str]) -> subprocess.CompletedProcess:
    """Helper to run specnut digest command."""
    cmd = ["poetry", "run", "python", "-m", "specnut", "digest"] + args
    return subprocess.run(cmd, capture_output=True, text=True)


class TestIncludeFlag:
    """T040-T042: Contract tests for --include flag."""

    def test_include_flag_adds_extensions(self, tmp_path):
        """T040: Verify --include flag processes custom file extensions."""
        # Create files with different extensions
        (tmp_path / "spec.md").write_text(SAMPLE_SPEC)
        (tmp_path / "spec.txt").write_text(SAMPLE_SPEC)
        (tmp_path / "spec.pdf").write_text("Binary PDF content")

        # Process with --include "*.txt"
        result = run_digest([str(tmp_path), "--include", "*.txt"])

        # Should process .md (default) and .txt (included)
        assert result.returncode == 0, f"Failed: {result.stdout}"
        assert (tmp_path / "spec.digest.md").exists(), "Should process .md (default)"
        assert (tmp_path / "spec.digest.txt").exists(), "Should process .txt (included)"
        assert not (tmp_path / "spec.digest.pdf").exists(), "Should NOT process .pdf"

    def test_include_flag_multiple_patterns(self, tmp_path):
        """T041: Verify multiple --include flags work together."""
        # Create files with different extensions
        (tmp_path / "spec.md").write_text(SAMPLE_SPEC)
        (tmp_path / "requirements.spec").write_text(SAMPLE_SPEC)
        (tmp_path / "features.requirements").write_text(SAMPLE_SPEC)
        (tmp_path / "readme.txt").write_text("Readme content")

        # Process with multiple --include patterns
        result = run_digest([
            str(tmp_path),
            "--include", "*.spec",
            "--include", "*.requirements"
        ])

        # Should process .md (default), .spec, and .requirements
        assert result.returncode == 0
        assert (tmp_path / "spec.digest.md").exists()
        assert (tmp_path / "requirements.digest.spec").exists()
        assert (tmp_path / "features.digest.requirements").exists()
        assert not (tmp_path / "readme.digest.txt").exists()

    def test_include_preserves_defaults(self, tmp_path):
        """T042: Verify --include doesn't remove default extensions."""
        # Create files with default extensions
        (tmp_path / "spec1.md").write_text(SAMPLE_SPEC)
        (tmp_path / "spec2.md").write_text(SAMPLE_SPEC)
        (tmp_path / "custom.txt").write_text(SAMPLE_SPEC)

        # Process with --include "*.txt"
        result = run_digest([str(tmp_path), "--include", "*.txt"])

        # Should process ALL defaults (.md) PLUS custom (.txt)
        assert result.returncode == 0
        assert (tmp_path / "spec1.digest.md").exists(), "Default .md should be processed"
        assert (tmp_path / "spec2.digest.md").exists(), "Default .md should be processed"
        assert (tmp_path / "custom.digest.txt").exists(), "Custom .txt should be processed"


class TestNoRecursiveFlag:
    """T043-T045: Contract tests for --no-recursive flag."""

    def test_no_recursive_flag_limits_depth(self, tmp_path):
        """T043: Verify --no-recursive only processes top-level files."""
        # Create nested structure
        (tmp_path / "top.md").write_text(SAMPLE_SPEC)

        subdir = tmp_path / "nested"
        subdir.mkdir()
        (subdir / "deep.md").write_text(SAMPLE_SPEC)

        # Process with --no-recursive
        result = run_digest([str(tmp_path), "--no-recursive"])

        # Should process top-level only
        assert result.returncode == 0
        assert (tmp_path / "top.digest.md").exists(), "Top-level file should be processed"
        assert not (subdir / "deep.digest.md").exists(), "Nested file should NOT be processed"

    def test_no_recursive_skips_subdirectories(self, tmp_path):
        """T044: Verify --no-recursive ignores all subdirectories."""
        # Create multiple subdirectories
        (tmp_path / "root.md").write_text(SAMPLE_SPEC)

        for dirname in ["dir1", "dir2", "dir3"]:
            dirpath = tmp_path / dirname
            dirpath.mkdir()
            (dirpath / f"{dirname}.md").write_text(SAMPLE_SPEC)

        # Process with --no-recursive
        result = run_digest([str(tmp_path), "--no-recursive"])

        # Should only process root file
        assert result.returncode == 0
        assert (tmp_path / "root.digest.md").exists()
        assert not (tmp_path / "dir1" / "dir1.digest.md").exists()
        assert not (tmp_path / "dir2" / "dir2.digest.md").exists()
        assert not (tmp_path / "dir3" / "dir3.digest.md").exists()

    def test_recursive_default_behavior(self, tmp_path):
        """T045: Verify recursive scanning is enabled by default."""
        # Create 3-level deep structure
        (tmp_path / "level0.md").write_text(SAMPLE_SPEC)

        level1 = tmp_path / "level1"
        level1.mkdir()
        (level1 / "level1.md").write_text(SAMPLE_SPEC)

        level2 = level1 / "level2"
        level2.mkdir()
        (level2 / "level2.md").write_text(SAMPLE_SPEC)

        # Process WITHOUT --no-recursive (default recursive=True)
        result = run_digest([str(tmp_path)])

        # Should process ALL levels by default
        assert result.returncode == 0
        assert (tmp_path / "level0.digest.md").exists()
        assert (level1 / "level1.digest.md").exists()
        assert (level2 / "level2.digest.md").exists()
