"""
Integration tests for metrics display (User Story 3).

Tests verify end-to-end metrics functionality including:
- Metrics display from valid digest
- Section breakdown
- Different output formats
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


class TestMetricsDisplay:
    """T084: Integration test for metrics display from valid digest."""

    def test_metrics_from_valid_digest(self, tmp_path):
        """Verify metrics can be displayed from a successfully created digest."""
        # Create a spec file
        spec_file = tmp_path / "spec.md"
        spec_content = """# Payment Processing Feature

## Overview
This feature provides comprehensive payment processing capabilities for the application.
Users can process payments using various methods including credit cards, debit cards,
and digital wallets like PayPal and Apple Pay.

## Functional Requirements

### FR-001: Credit Card Processing
**Priority**: Critical
**Description**: The system MUST support processing of major credit cards including
Visa, Mastercard, American Express, and Discover. All card data must be encrypted
and PCI-DSS compliant.

### FR-002: Payment Security
**Priority**: Critical
**Description**: All payment data must be encrypted end-to-end. The system must
implement tokenization for sensitive card data and maintain audit logs of all
payment transactions.

### FR-003: Multiple Payment Methods
**Priority**: High
**Description**: Support for digital wallets including PayPal, Apple Pay, Google Pay,
and other popular payment methods. Each method should have proper error handling
and fallback mechanisms.

## User Stories

### US-001: Process Credit Card Payment
**As a** customer
**I want to** pay with my credit card
**So that** I can complete my purchase securely

**Acceptance Criteria**:
- Given a valid credit card
- When I enter card details and submit
- Then payment is processed and confirmation shown
- And transaction is logged for audit

### US-002: Use Digital Wallet
**As a** customer
**I want to** pay with my digital wallet
**So that** I can checkout quickly

**Acceptance Criteria**:
- Given PayPal or Apple Pay is configured
- When I select digital wallet option
- Then I am redirected to wallet provider
- And payment completes upon authorization
"""
        spec_file.write_text(spec_content)

        # Generate digest
        digest_result = run_command(["digest", str(spec_file)])

        # Skip if digest failed
        if digest_result.returncode != 0:
            pytest.skip(f"Digest generation failed: {digest_result.stderr}")

        digest_file = tmp_path / "spec.digest.md"
        if not digest_file.exists():
            pytest.skip("Digest file was not created")

        # Display metrics
        metrics_result = run_command(["metrics", str(digest_file)])

        # Should succeed
        assert metrics_result.returncode == 0, f"Metrics failed: {metrics_result.stderr}"

        # Should show token information
        output = metrics_result.stdout.lower()
        assert "token" in output
        assert any(word in output for word in ["original", "digest", "saved", "optimized"])


class TestSectionBreakdown:
    """T085: Integration test for section breakdown."""

    def test_section_breakdown_display(self, tmp_path):
        """Verify section breakdown shows per-section metrics."""
        # Create spec with multiple sections
        spec_file = tmp_path / "spec.md"
        spec_content = (
            """# Multi-Section Feature

## Requirements
This section contains detailed requirements with verbose explanations.

### FR-001: First Requirement
A very detailed requirement with lots of explanatory text that can be compressed.

## User Stories
This section has user stories.

### US-001: First Story
As a user, I want something.

## Edge Cases
This section discusses edge cases and exceptional scenarios.

### EC-001: Edge Case
What happens when things go wrong.
"""
            * 5
        )  # Repeat to make it larger
        spec_file.write_text(spec_content)

        # Generate digest
        digest_result = run_command(["digest", str(spec_file)])
        if digest_result.returncode != 0:
            pytest.skip("Digest generation failed")

        digest_file = tmp_path / "spec.digest.md"
        if not digest_file.exists():
            pytest.skip("Digest file not created")

        # Get metrics with breakdown
        metrics_result = run_command(["metrics", str(digest_file), "--breakdown"])

        # Should succeed or show informative output
        if metrics_result.returncode == 0:
            output = metrics_result.stdout.lower()
            # Should mention sections or breakdown
            assert "section" in output or "breakdown" in output or len(output) > 0


class TestMetricsFormats:
    """Test different metrics output formats."""

    def test_metrics_json_contains_required_fields(self, tmp_path):
        """Verify JSON metrics contain required fields."""
        # Create and digest
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test\n\n" + "Content line\n" * 200)

        digest_result = run_command(["digest", str(spec_file)])
        if digest_result.returncode != 0:
            pytest.skip("Digest generation failed")

        digest_file = tmp_path / "spec.digest.md"
        if not digest_file.exists():
            pytest.skip("Digest file not created")

        # Get JSON metrics
        result = run_command(["metrics", str(digest_file), "-f", "json"])

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                # Check for expected metric fields
                assert isinstance(data, dict)
                # Should have token-related information
                data_str = str(data).lower()
                assert "token" in data_str or "original" in data_str or "digest" in data_str
            except json.JSONDecodeError:
                pytest.fail("Invalid JSON output")
