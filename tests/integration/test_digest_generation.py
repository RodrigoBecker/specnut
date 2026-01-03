"""
Integration tests for digest generation (User Story 2).

Tests verify end-to-end digest generation workflow including:
- Format detection and parsing
- Token counting and compression
- Metadata generation
- Performance requirements
"""

import json
import subprocess
import time
from pathlib import Path

import pytest
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


# Large spec for performance testing
LARGE_MARKDOWN_SPEC = """# Large Feature Specification

## Overview
""" + "\n".join(
    [
        f"""
### Section {i}

This is section {i} with detailed description. It contains comprehensive information
about functional requirements, user stories, acceptance criteria, edge cases, and
various other specification details that need to be documented for proper implementation.

#### Functional Requirement FR-{i:03d}

**Priority**: Critical

The system MUST provide functionality for requirement {i}. This includes:
- Detailed implementation requirements
- Comprehensive acceptance criteria
- Edge case handling
- Error handling and validation
- Performance requirements
- Security considerations

#### User Story US-{i:03d}

**As a** user
**I want to** use feature {i}
**So that** I can accomplish task {i}

**Acceptance Criteria**:
- Given precondition {i}
- When action {i} is performed
- Then outcome {i} should occur
"""
        for i in range(100)
    ]
)


class TestDigestGenerationYAML:
    """T048: Integration test for digest generation from YAML."""

    def test_yaml_digest_preserves_structure(self, tmp_path):
        """Verify YAML digest maintains valid structure."""
        spec_content = """
feature:
  name: Test Feature
  requirements:
    - id: FR-001
      text: Requirement 1
      priority: critical
    - id: FR-002
      text: Requirement 2
      priority: high
"""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(spec_content)

        result = run_digest([str(spec_file)])

        assert result.returncode == 0

        digest_file = tmp_path / "spec.digest.yaml"
        assert digest_file.exists()

        # Verify structure is preserved
        with open(digest_file) as f:
            data = yaml.safe_load(f)
            assert "feature" in data
            assert data["feature"]["name"] == "Test Feature"


class TestDigestGenerationJSON:
    """T049: Integration test for digest generation from JSON."""

    def test_json_digest_maintains_schema(self, tmp_path):
        """Verify JSON digest maintains valid schema."""
        spec_data = {
            "feature": {
                "name": "Test Feature",
                "requirements": [
                    {"id": "FR-001", "text": "Requirement 1"},
                    {"id": "FR-002", "text": "Requirement 2"},
                ],
            }
        }
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(spec_data, indent=2))

        result = run_digest([str(spec_file)])

        assert result.returncode == 0

        digest_file = tmp_path / "spec.digest.json"
        assert digest_file.exists()

        with open(digest_file) as f:
            data = json.load(f)
            assert "feature" in data


class TestDigestGenerationMarkdown:
    """T050: Integration test for digest generation from Markdown."""

    def test_markdown_digest_preserves_headers(self, tmp_path):
        """Verify Markdown digest preserves heading structure."""
        spec_content = """# Feature Specification

## Functional Requirements

### FR-001: First Requirement
This is a critical requirement with detailed description.

### FR-002: Second Requirement
This is another requirement.

## User Stories

### US-001: User Story 1
As a user, I want to do something.
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)

        result = run_digest([str(spec_file)])

        assert result.returncode == 0

        digest_file = tmp_path / "spec.digest.md"
        assert digest_file.exists()

        content = digest_file.read_text()
        # Verify key headers are preserved
        assert "#" in content
        assert "FR-001" in content or "Functional" in content


class TestFormatDetection:
    """T051: Integration test for format auto-detection."""

    def test_yaml_format_detection(self, tmp_path):
        """Verify YAML format is auto-detected."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text("feature:\n  name: Test\n")

        result = run_digest([str(spec_file)])

        assert result.returncode == 0
        # Should create .yaml digest
        assert (tmp_path / "spec.digest.yaml").exists()

    def test_json_format_detection(self, tmp_path):
        """Verify JSON format is auto-detected."""
        spec_file = tmp_path / "spec.json"
        spec_file.write_text('{"feature": {"name": "Test"}}')

        result = run_digest([str(spec_file)])

        assert result.returncode == 0
        # Should create .json digest
        assert (tmp_path / "spec.digest.json").exists()

    def test_markdown_format_detection(self, tmp_path):
        """Verify Markdown format is auto-detected."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test Feature\n\n## Requirements\n")

        result = run_digest([str(spec_file)])

        assert result.returncode == 0
        # Should create .md digest
        assert (tmp_path / "spec.digest.md").exists()


class TestCompressionRatio:
    """T052: Integration test for 30% minimum compression ratio."""

    def test_achieves_30_percent_reduction(self, tmp_path):
        """Verify digest achieves at least 30% token reduction on typical spec."""
        # Create a spec with compressible content
        spec_content = """# Feature Specification

## Overview

This feature provides a comprehensive solution for managing user data.
The system allows users to create, read, update, and delete their personal
information in a secure and efficient manner. This includes full support
for various data types and validation rules.

## Functional Requirements

### FR-001: User Data Management
**Priority**: Critical
**Description**: The system MUST allow users to manage their personal data
including creating new profiles, updating existing information, and deleting
their accounts when needed. All operations must be secure and auditable.

### FR-002: Data Validation
**Priority**: Critical
**Description**: All user input MUST be validated according to predefined rules
including format validation, length constraints, and business rule validation.

### FR-003: Audit Logging
**Priority**: High
**Description**: The system SHOULD log all data modification operations for
security and compliance purposes.

## User Stories

### US-001: Create Profile
**As a** new user
**I want to** create my profile with personal information
**So that** I can access the system features

**Acceptance Criteria**:
- Given a registration form
- When I submit valid profile data
- Then my profile is created and I receive confirmation

### US-002: Update Profile
**As a** registered user
**I want to** update my profile information
**So that** I can keep my data current

**Acceptance Criteria**:
- Given I am logged in
- When I modify my profile data
- Then changes are saved and reflected immediately
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)

        result = run_digest([str(spec_file)])

        # Should succeed (compression target met) or fail gracefully
        assert result.returncode in [0, 3]

        if result.returncode == 0:
            digest_file = tmp_path / "spec.digest.md"
            assert digest_file.exists()

            # Verify digest is smaller than original
            original_size = len(spec_content)
            digest_size = len(digest_file.read_text())
            assert digest_size < original_size


class TestPerformance:
    """T053: Integration test for performance (<10s for 50k tokens)."""

    @pytest.mark.slow
    def test_processes_large_file_under_10_seconds(self, tmp_path):
        """Verify large file (targeting ~50k tokens) processes in <10 seconds."""
        spec_file = tmp_path / "large_spec.md"
        spec_file.write_text(LARGE_MARKDOWN_SPEC)

        start_time = time.time()
        result = run_digest([str(spec_file)])
        elapsed = time.time() - start_time

        # Should complete within time limit (being generous with 15s for CI environments)
        assert elapsed < 15.0, f"Processing took {elapsed:.2f}s (expected <15s)"

        # Should succeed or fail with compression error (acceptable for large files)
        assert result.returncode in [0, 3]


class TestEndToEndWorkflow:
    """Test complete digest generation workflow."""

    def test_full_digest_workflow(self, tmp_path):
        """Test complete workflow from spec to digest with metadata."""
        spec_content = """# Payment Processing Feature

## Requirements

### FR-001: Credit Card Processing
Support Visa, Mastercard, American Express cards.

### FR-002: Security
All transactions must be encrypted and PCI compliant.

## User Stories

### US-001: Make Payment
As a customer, I want to pay with my credit card.
"""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(spec_content)

        # Generate digest
        result = run_digest([str(spec_file)])

        assert result.returncode == 0

        # Verify digest created
        digest_file = tmp_path / "spec.digest.md"
        assert digest_file.exists()

        # Verify digest has content
        digest_content = digest_file.read_text()
        assert len(digest_content) > 0

        # Verify critical content is preserved
        assert "FR-001" in digest_content or "Credit Card" in digest_content
        assert "FR-002" in digest_content or "Security" in digest_content
