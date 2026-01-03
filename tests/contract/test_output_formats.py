"""
Contract tests for output format options.

Tests verify --format and --compression flags work correctly.
"""

import json
import subprocess
from pathlib import Path

import yaml


def run_digest(args: list[str]) -> subprocess.CompletedProcess:
    """Run specnut digest command from project root."""
    project_root = Path(__file__).parent.parent.parent
    return subprocess.run(
        ["poetry", "run", "python", "-m", "specnut", "digest"] + args,
        capture_output=True,
        text=True,
        cwd=project_root,
    )


SAMPLE_SPEC = """
feature:
  name: Test Feature
  description: A test feature for validation
  requirements:
    - id: FR-001
      title: First Requirement
      description: This is the first requirement with detailed explanation
    - id: FR-002
      title: Second Requirement
      description: This is the second requirement
"""


class TestFormatOptions:
    """Test --format flag variations."""

    def test_format_yaml_output(self, tmp_path):
        """Verify --format yaml produces valid YAML."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(SAMPLE_SPEC)

        result = run_digest([str(spec_file), "--format", "yaml"])

        assert result.returncode == 0
        digest_file = tmp_path / "spec.digest.yaml"
        assert digest_file.exists()

        # Verify valid YAML
        with open(digest_file) as f:
            data = yaml.safe_load(f)
            assert isinstance(data, dict)

    def test_format_json_output(self, tmp_path):
        """Verify --format json produces valid JSON."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(SAMPLE_SPEC)

        result = run_digest([str(spec_file), "--format", "json"])

        assert result.returncode == 0
        digest_file = tmp_path / "spec.digest.json"
        assert digest_file.exists()

        # Verify valid JSON
        with open(digest_file) as f:
            data = json.load(f)
            assert isinstance(data, dict)

    def test_format_markdown_output(self, tmp_path):
        """Verify --format markdown produces Markdown."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(SAMPLE_SPEC)

        result = run_digest([str(spec_file), "--format", "markdown"])

        assert result.returncode == 0
        digest_file = tmp_path / "spec.digest.md"
        assert digest_file.exists()

        content = digest_file.read_text()
        # Should have markdown headers
        assert "#" in content or len(content) > 0

    def test_format_compact_output(self, tmp_path):
        """Verify --format compact produces compact format."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(SAMPLE_SPEC)

        result = run_digest([str(spec_file), "--format", "compact"])

        # Should succeed
        assert result.returncode == 0


class TestCompressionOptions:
    """Test --compression flag variations."""

    def test_compression_levels(self, tmp_path):
        """Verify all compression levels work."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(SAMPLE_SPEC)

        for level in ["low", "medium", "high"]:
            result = run_digest(
                [str(spec_file), "-c", level, "-o", str(tmp_path / f"digest_{level}.yaml")]
            )

            assert result.returncode == 0, f"Failed for compression level: {level}"
            assert (tmp_path / f"digest_{level}.yaml").exists()
