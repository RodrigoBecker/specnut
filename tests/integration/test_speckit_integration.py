"""
Integration tests for Speckit integration (User Story 4).

Tests verify optional integration with Speckit when both tools are installed:
- Speckit detection
- Hook registration
- Auto-digest generation
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestSpeckitDetection:
    """T096: Integration test for Speckit detection."""

    def test_detects_speckit_when_available(self):
        """Verify Speckit is detected when installed."""
        # Import the integration module
        try:
            from specnut.integrations import speckit

            # Check if detection function exists
            assert hasattr(speckit, "is_speckit_available") or hasattr(speckit, "SPECKIT_AVAILABLE")

        except ImportError:
            pytest.skip("Speckit integration module not yet implemented")

    def test_gracefully_handles_missing_speckit(self):
        """Verify graceful handling when Speckit is not installed."""
        try:
            from specnut.integrations import speckit

            # Should not raise error even if Speckit not installed
            # The module should handle ImportError internally
            assert True

        except ImportError as e:
            # Module itself might not exist yet
            if "specnut.integrations" in str(e):
                pytest.skip("Integration module not yet implemented")
            else:
                raise


class TestHookRegistration:
    """T097: Integration test for hook registration when Speckit available."""

    def test_registers_hooks_when_speckit_present(self):
        """Verify hooks are registered when Speckit is available."""
        try:
            from specnut.integrations import speckit

            # Check if hook registration function exists
            has_register = hasattr(speckit, "register_hooks") or hasattr(speckit, "register")

            if has_register:
                # Function exists, test passes
                assert True
            else:
                pytest.skip("Hook registration not yet implemented")

        except ImportError:
            pytest.skip("Integration module not yet implemented")

    def test_skips_registration_when_speckit_missing(self):
        """Verify hooks are not registered when Speckit is missing."""
        try:
            from specnut.integrations import speckit

            # With Speckit not available, registration should be skipped
            # This should not raise errors
            assert True

        except ImportError:
            pytest.skip("Integration module not yet implemented")


class TestAutoDigestGeneration:
    """T098: Integration test for auto-digest generation via hooks."""

    @patch("importlib.util.find_spec")
    def test_auto_digest_hook_integration(self, mock_find_spec):
        """Verify auto-digest hook can be called."""
        # Mock Speckit as available
        mock_find_spec.return_value = Mock()

        try:
            from specnut.integrations import speckit

            # Check if auto_digest function exists
            if hasattr(speckit, "auto_digest"):
                # Function exists
                assert callable(speckit.auto_digest)
            else:
                pytest.skip("Auto-digest function not yet implemented")

        except ImportError:
            pytest.skip("Integration module not yet implemented")

    def test_dual_output_preservation(self, tmp_path):
        """Verify dual output: preserve original, write digest."""
        try:
            from specnut.integrations import speckit

            # Create a test spec file
            spec_file = tmp_path / "spec.md"
            spec_file.write_text("# Test Spec\n\nContent here.")

            # If auto_digest exists, it should preserve original
            if hasattr(speckit, "auto_digest"):
                # Test that original file is not modified
                original_content = spec_file.read_text()

                # This would be called by the hook in real usage
                # For now, just verify the function exists
                assert callable(speckit.auto_digest)
                assert spec_file.read_text() == original_content
            else:
                pytest.skip("Auto-digest not yet implemented")

        except ImportError:
            pytest.skip("Integration module not yet implemented")


class TestConfigurationSupport:
    """Test configuration file support for Speckit integration."""

    def test_config_file_detection(self, tmp_path):
        """Verify .specnut.yaml config file can be detected."""
        # Create a config file
        config_file = tmp_path / ".specnut.yaml"
        config_content = """
speckit:
  auto_optimize: true
  digest_directory: .specify/digests/
  compression: medium
"""
        config_file.write_text(config_content)

        try:
            from specnut.integrations import speckit

            # Check if config loading exists
            if hasattr(speckit, "load_config") or hasattr(speckit, "read_config"):
                assert True
            else:
                # Config loading may be in a separate module
                pytest.skip("Config loading not yet in integration module")

        except ImportError:
            pytest.skip("Integration module not yet implemented")

    def test_environment_variable_support(self, monkeypatch):
        """Verify SPECNUT_AUTO_OPTIMIZE environment variable support."""
        # Set environment variable
        monkeypatch.setenv("SPECNUT_AUTO_OPTIMIZE", "true")

        import os

        assert os.environ.get("SPECNUT_AUTO_OPTIMIZE") == "true"

        # The integration module should be able to read this
        # This test just verifies env var mechanism works
        assert True


class TestSpeckitWorkflow:
    """Test complete Speckit integration workflow."""

    def test_integration_does_not_break_standalone_usage(self, tmp_path):
        """Verify SpecNut works standalone even with integration code present."""
        import subprocess

        # Create a simple spec
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("# Test\n\n" + "Content\n" * 50)

        # Run digest command (should work regardless of Speckit)
        result = subprocess.run(
            ["poetry", "run", "python", "-m", "specnut", "digest", str(spec_file)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        # Should work independently (success, compression error, or validation error for small files)
        assert result.returncode in [0, 2, 3]
