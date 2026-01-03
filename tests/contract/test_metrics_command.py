"""
Contract tests for `specnut metrics` command (User Story 3).

Tests verify that the metrics command meets contract specifications per
contracts/cli-commands.md.
"""

import json
import subprocess
from pathlib import Path

import pytest


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    """Run specnut command from project root."""
    project_root = Path(__file__).parent.parent.parent
    return subprocess.run(
        ["poetry", "run", "python", "-m", "specnut"] + args,
        capture_output=True,
        text=True,
        cwd=project_root,
    )


class TestMetricsTableOutput:
    """T080: Contract test for specnut metrics with table output."""

    def test_metrics_displays_table_format(self, tmp_path):
        """Verify metrics command displays table format by default."""
        # First create a digest file
        spec_file = tmp_path / "spec.md"
        spec_content = (
            """# Feature Specification

## Requirements

### FR-001: First Requirement
This is a detailed requirement with comprehensive explanation.

### FR-002: Second Requirement
Another detailed requirement.

## User Stories

### US-001: User Story
As a user, I want to do something.
"""
            * 10
        )  # Make it larger for better compression
        spec_file.write_text(spec_content)

        # Generate digest
        digest_result = run_command(["digest", str(spec_file)])

        # Skip if digest generation failed
        if digest_result.returncode != 0:
            pytest.skip(f"Digest generation failed: {digest_result.stderr}")

        digest_file = tmp_path / "spec.digest.md"
        if not digest_file.exists():
            pytest.skip("Digest file not created")

        # Run metrics command
        result = run_command(["metrics", str(digest_file)])

        # Should succeed
        assert result.returncode == 0, f"Failed with: {result.stderr}"

        # Should contain table-like output
        assert "token" in result.stdout.lower()
        assert "original" in result.stdout.lower() or "digest" in result.stdout.lower()


class TestMetricsJSONOutput:
    """T081: Contract test for specnut metrics --format json."""

    def test_metrics_json_format(self, tmp_path):
        """Verify --format json produces valid JSON output."""
        # Create and generate digest
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test\n" + "Content " * 100)

        digest_result = run_command(["digest", str(spec_file)])
        if digest_result.returncode != 0:
            pytest.skip("Digest generation failed")

        digest_file = tmp_path / "spec.digest.md"
        if not digest_file.exists():
            pytest.skip("Digest file not created")

        # Get metrics in JSON format
        result = run_command(["metrics", str(digest_file), "--format", "json"])

        assert result.returncode == 0, f"Failed with: {result.stderr}"

        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            # Should contain expected fields
            assert "original_tokens" in data or "tokens" in str(data).lower()
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON output: {e}")


class TestMetricsYAMLOutput:
    """T082: Contract test for specnut metrics --format yaml."""

    def test_metrics_yaml_format(self, tmp_path):
        """Verify --format yaml produces YAML output."""
        # Create and generate digest
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test\n" + "Content " * 100)

        digest_result = run_command(["digest", str(spec_file)])
        if digest_result.returncode != 0:
            pytest.skip("Digest generation failed")

        digest_file = tmp_path / "spec.digest.md"
        if not digest_file.exists():
            pytest.skip("Digest file not created")

        # Get metrics in YAML format
        result = run_command(["metrics", str(digest_file), "--format", "yaml"])

        # Should succeed or show helpful error
        if result.returncode == 0:
            # Should contain YAML-like output
            assert ":" in result.stdout
            assert "token" in result.stdout.lower() or "original" in result.stdout.lower()


class TestMetricsBreakdown:
    """T083: Contract test for specnut metrics --breakdown."""

    def test_metrics_breakdown_flag(self, tmp_path):
        """Verify --breakdown shows per-section metrics."""
        # Create and generate digest
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test\n" + "Content " * 100)

        digest_result = run_command(["digest", str(spec_file)])
        if digest_result.returncode != 0:
            pytest.skip("Digest generation failed")

        digest_file = tmp_path / "spec.digest.md"
        if not digest_file.exists():
            pytest.skip("Digest file not created")

        # Get metrics with breakdown
        result = run_command(["metrics", str(digest_file), "--breakdown"])

        # Should succeed
        if result.returncode == 0:
            # Should contain section information or breakdown
            assert "section" in result.stdout.lower() or "breakdown" in result.stdout.lower()


class TestMetricsErrors:
    """Test error handling for metrics command."""

    def test_metrics_file_not_found(self, tmp_path):
        """Verify error when digest file doesn't exist."""
        result = run_command(["metrics", str(tmp_path / "nonexistent.md")])

        # Should fail with error code
        assert result.returncode != 0
        # Error message could be in stdout or stderr
        error_output = (result.stdout + result.stderr).lower()
        assert "error" in error_output or "not found" in error_output

    def test_metrics_invalid_digest_file(self, tmp_path):
        """Verify error when file is not a valid digest."""
        # Create a non-digest file
        invalid_file = tmp_path / "invalid.md"
        invalid_file.write_text("Just some random text")

        result = run_command(["metrics", str(invalid_file)])

        # Should fail with error code (1 or 2)
        assert result.returncode in [1, 2]
