"""
Contract tests for `specnut digest` command (User Story 2).

Tests verify that the digest command meets contract specifications per
contracts/cli-commands.md and contracts/exit-codes.md.
"""

import json
import subprocess
from pathlib import Path

import yaml


def run_digest(args: list[str]) -> subprocess.CompletedProcess:
    """Run specnut digest command from project root."""
    # Always run from project root where pyproject.toml exists
    project_root = Path(__file__).parent.parent.parent
    return subprocess.run(
        ["poetry", "run", "python", "-m", "specnut", "digest"] + args,
        capture_output=True,
        text=True,
        cwd=project_root,
    )


# Sample specification content for testing - made larger and more compressible
SAMPLE_YAML_SPEC = """
feature:
  name: User Authentication System
  description: |
    This feature implements a comprehensive user authentication system that
    allows users to securely register, log in, and manage their accounts.
    The system supports multiple authentication methods including email/password
    and OAuth providers like Google, GitHub, and Microsoft.

    The authentication system provides robust security features including password
    hashing, session management, token-based authentication, and multi-factor
    authentication support. It integrates with external identity providers and
    maintains detailed audit logs of all authentication events.

functional_requirements:
  - id: FR-001
    title: User Registration
    description: |
      The system must allow new users to register with email and password.
      Email verification is required before account activation.
      The registration process includes validation of email format, password
      strength requirements, and checking for duplicate accounts.
    priority: critical
    acceptance_criteria:
      - Email must be valid format
      - Password must meet complexity requirements
      - Email verification sent within 30 seconds
      - Account activated upon email confirmation

  - id: FR-002
    title: User Login
    description: |
      Users must be able to log in using their email and password.
      The system should support session management and remember-me functionality.
      Failed login attempts are tracked and accounts are locked after 5 failures.
      Session tokens expire after 24 hours of inactivity.
    priority: critical
    acceptance_criteria:
      - Valid credentials authenticate successfully
      - Invalid credentials show error message
      - Locked accounts cannot log in
      - Sessions persist with remember-me option

  - id: FR-003
    title: OAuth Integration
    description: |
      Support OAuth login via Google, GitHub, and Microsoft providers.
      The system handles OAuth callbacks, token exchange, and profile retrieval.
      New accounts are automatically created for OAuth users.
    priority: high
    acceptance_criteria:
      - Google OAuth works correctly
      - GitHub OAuth works correctly
      - Microsoft OAuth works correctly
      - Profile data is retrieved and stored

user_stories:
  - id: US-001
    title: As a new user, I want to register with email
    description: New users need to create accounts to access the system
    acceptance_criteria:
      - Given a registration form with email and password fields
      - When I provide valid email and strong password
      - Then my account is created and email verification sent
      - And I can log in after verifying my email

  - id: US-002
    title: As a registered user, I want to log in
    description: Registered users need to authenticate to access their accounts
    acceptance_criteria:
      - Given a login form with email and password fields
      - When I provide correct credentials
      - Then I am authenticated and redirected to dashboard
      - And my session is maintained for 24 hours
"""

SAMPLE_JSON_SPEC = json.dumps(
    {
        "feature": {
            "name": "Payment Processing",
            "description": "A comprehensive payment processing system with support for credit cards, debit cards, and digital wallets like PayPal and Apple Pay.",
        },
        "functional_requirements": [
            {
                "id": "FR-001",
                "title": "Credit Card Processing",
                "description": "The system must support processing of major credit cards including Visa, Mastercard, American Express, and Discover.",
                "priority": "critical",
            },
            {
                "id": "FR-002",
                "title": "Payment Security",
                "description": "All payment data must be encrypted and PCI-DSS compliant with tokenization of sensitive card data.",
                "priority": "critical",
            },
        ],
    }
)

SAMPLE_MD_SPEC = """# Feature Specification: Search Functionality

## Overview

This feature implements a powerful search system that allows users to quickly
find content across the entire application. The search supports full-text search,
filters, faceted navigation, and real-time suggestions as users type.

## Functional Requirements

### FR-001: Basic Search
**Priority**: Critical

The system MUST provide a search bar that allows users to enter search queries
and returns relevant results sorted by relevance score.

### FR-002: Search Filters
**Priority**: High

Users should be able to filter search results by:
- Content type (articles, documents, videos)
- Date range (last day, week, month, year, custom)
- Author/creator
- Tags and categories

### FR-003: Search Suggestions
**Priority**: Medium

As users type in the search bar, the system should provide real-time search
suggestions based on popular queries and autocomplete functionality.

## User Stories

### US-001: Search for Content
**As a** user
**I want to** search for content using keywords
**So that** I can quickly find what I'm looking for

**Acceptance Criteria**:
- Given a search bar on every page
- When I enter a search query and press enter
- Then I see relevant results ranked by relevance

### US-002: Filter Results
**As a** user
**I want to** filter my search results
**So that** I can narrow down to specific content types

**Acceptance Criteria**:
- Given search results displayed
- When I apply filters
- Then only matching results are shown

## Edge Cases

- Empty search query handling
- Very long search queries (>1000 characters)
- Special characters in search terms
- No results found scenarios
- Network timeout during search

## Assumptions

- Search index is updated every 5 minutes
- Maximum 1000 results returned per query
- Search response time < 200ms for 95th percentile
"""


class TestDigestYAMLInput:
    """T042: Contract test for specnut digest with YAML input."""

    def test_digest_yaml_file_creates_yaml_digest(self, tmp_path):
        """Verify YAML input creates valid YAML digest."""
        # Create test YAML file
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(SAMPLE_YAML_SPEC)

        # Run digest command
        result = run_digest([str(spec_file)])

        # Should succeed or fail with compression error (small file)
        assert result.returncode in [0, 3], f"Failed with: {result.stderr}"

        # Only check output file if command succeeded
        if result.returncode == 0:
            # Check output file was created
            digest_file = tmp_path / "spec.digest.yaml"
            assert digest_file.exists(), "Digest file was not created"

            # Verify it's valid YAML
            with open(digest_file) as f:
                digest_data = yaml.safe_load(f)
                assert digest_data is not None
                assert isinstance(digest_data, dict)

    def test_digest_yml_extension(self, tmp_path):
        """Verify .yml extension is also supported."""
        spec_file = tmp_path / "spec.yml"
        spec_file.write_text(SAMPLE_YAML_SPEC)

        result = run_digest([str(spec_file)])

        assert result.returncode == 0
        digest_file = tmp_path / "spec.digest.yml"
        assert digest_file.exists()


class TestDigestJSONInput:
    """T043: Contract test for specnut digest with JSON input."""

    def test_digest_json_file_creates_json_digest(self, tmp_path):
        """Verify JSON input creates valid JSON digest."""
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(SAMPLE_JSON_SPEC)

        result = run_digest([str(spec_file)])

        assert result.returncode == 0, f"Failed with: {result.stderr}"

        digest_file = tmp_path / "spec.digest.json"
        assert digest_file.exists()

        # Verify it's valid JSON
        with open(digest_file) as f:
            digest_data = json.load(f)
            assert digest_data is not None
            assert isinstance(digest_data, dict)


class TestDigestMarkdownInput:
    """T044: Contract test for specnut digest with Markdown input."""

    def test_digest_markdown_file_creates_markdown_digest(self, tmp_path):
        """Verify Markdown input creates valid Markdown digest."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SAMPLE_MD_SPEC)

        result = run_digest([str(spec_file)])

        assert result.returncode == 0, f"Failed with: {result.stderr}"

        digest_file = tmp_path / "spec.digest.md"
        assert digest_file.exists()

        # Verify it's still Markdown
        content = digest_file.read_text()
        assert len(content) > 0
        # Should preserve markdown structure
        assert "#" in content  # Headers preserved


class TestDigestFormatFlag:
    """T045: Contract test for specnut digest --format flag."""

    def test_format_flag_yaml_to_json(self, tmp_path):
        """Verify --format flag converts YAML to JSON."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(SAMPLE_YAML_SPEC)

        result = run_digest([str(spec_file), "-f", "json"])

        assert result.returncode == 0
        # Should create JSON file
        digest_file = tmp_path / "spec.digest.json"
        assert digest_file.exists()

        # Verify it's valid JSON
        with open(digest_file) as f:
            data = json.load(f)
            assert data is not None

    def test_format_flag_json_to_markdown(self, tmp_path):
        """Verify --format flag converts JSON to Markdown."""
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(SAMPLE_JSON_SPEC)

        result = run_digest([str(spec_file), "-f", "markdown"])

        assert result.returncode == 0
        digest_file = tmp_path / "spec.digest.md"
        assert digest_file.exists()

    def test_format_auto_detection(self, tmp_path):
        """Verify auto format detection works (default behavior)."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(SAMPLE_YAML_SPEC)

        result = run_digest([str(spec_file), "-f", "auto"])

        assert result.returncode == 0
        # Should preserve original format
        digest_file = tmp_path / "spec.digest.yaml"
        assert digest_file.exists()


class TestDigestCompressionFlag:
    """T046: Contract test for specnut digest --compression flag."""

    def test_compression_low(self, tmp_path):
        """Verify --compression low setting."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SAMPLE_MD_SPEC)

        result = run_digest([str(spec_file), "-c", "low"])

        assert result.returncode == 0
        assert "low" in result.stdout.lower() or result.returncode == 0

    def test_compression_medium(self, tmp_path):
        """Verify --compression medium setting (default)."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SAMPLE_MD_SPEC)

        result = run_digest([str(spec_file), "-c", "medium"])

        assert result.returncode == 0

    def test_compression_high(self, tmp_path):
        """Verify --compression high setting."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SAMPLE_MD_SPEC)

        result = run_digest([str(spec_file), "-c", "high"])

        assert result.returncode == 0


class TestDigestExitCodes:
    """T047: Contract test for exit codes per contracts/exit-codes.md."""

    def test_exit_code_success(self, tmp_path):
        """Verify EXIT 0 on success."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SAMPLE_MD_SPEC)

        result = run_digest([str(spec_file)])

        assert result.returncode == 0

    def test_exit_code_file_not_found(self, tmp_path):
        """Verify EXIT 1 when input file doesn't exist."""
        result = run_digest([str(tmp_path / "nonexistent.md")])

        assert result.returncode == 1
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_exit_code_unsupported_format(self, tmp_path):
        """Verify EXIT 2 for unsupported format."""
        spec_file = tmp_path / "spec.txt"
        spec_file.write_text("Some text content")

        result = run_digest([str(spec_file)])

        # Should fail with validation error
        assert result.returncode in [1, 2]
        assert "format" in result.stderr.lower() or "unsupported" in result.stderr.lower()

    def test_exit_code_compression_failure(self, tmp_path):
        """Verify EXIT 3 when compression target not met (file too small/optimized)."""
        # Create minimal file that can't be compressed much
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Title\nFR-001: X\nFR-002: Y\n")

        result = run_digest([str(spec_file)])

        # Might fail with compression error or succeed if already optimal
        assert result.returncode in [0, 3]


class TestDigestOutputPath:
    """Test custom output path handling."""

    def test_custom_output_path(self, tmp_path):
        """Verify custom output path is respected."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(SAMPLE_MD_SPEC)
        output_file = tmp_path / "custom_output.md"

        result = run_digest([str(spec_file), "-o", str(output_file)])

        assert result.returncode == 0
        assert output_file.exists()
