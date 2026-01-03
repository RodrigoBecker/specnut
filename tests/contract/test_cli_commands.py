"""
Contract tests for CLI commands (User Story 1).

Tests verify that the CLI commands meet their contract specifications:
- specnut --help displays help text
- specnut --version shows version
- specnut version command works
"""

import subprocess



def run_command(args: list[str]) -> subprocess.CompletedProcess:
    """Run a specnut command and return the result."""
    return subprocess.run(
        ["python", "-m", "specnut"] + args,
        capture_output=True,
        text=True,
    )


class TestGlobalOptions:
    """Test global CLI options (--help, --version)."""

    def test_help_flag_displays_help_text(self):
        """T028: Contract test for `specnut --help` displays help text."""
        result = run_command(["--help"])

        assert result.returncode == 0
        assert "specnut" in result.stdout.lower()
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()
        # Check for main commands
        assert "digest" in result.stdout.lower()
        assert "version" in result.stdout.lower()

    def test_version_flag_shows_version(self):
        """T029: Contract test for `specnut --version` shows version."""
        result = run_command(["--version"])

        assert result.returncode == 0
        # Should show version number
        assert "0.1.0" in result.stdout or "version" in result.stdout.lower()


class TestVersionCommand:
    """Test the `specnut version` command."""

    def test_version_command_text_output(self):
        """T030: Contract test for `specnut version` command (text format)."""
        result = run_command(["version"])

        assert result.returncode == 0
        # Should show SpecNut version
        assert "specnut" in result.stdout.lower() or "0.1.0" in result.stdout
        # Should show Python version
        assert "python" in result.stdout.lower()

    def test_version_command_json_output(self):
        """T030: Contract test for `specnut version` command (JSON format)."""
        result = run_command(["version", "--format", "json"])

        assert result.returncode == 0
        # Should be valid JSON with version info
        assert "{" in result.stdout
        assert "}" in result.stdout
        # Should contain version fields
        assert "version" in result.stdout.lower() or "0.1.0" in result.stdout


class TestInstallation:
    """Integration test for CLI installation and access."""

    def test_cli_accessible_via_python_module(self):
        """T031: Integration test - CLI is accessible via python -m specnut."""
        result = run_command(["--help"])

        assert result.returncode == 0
        assert result.stderr == "" or "usage" in result.stderr.lower()
        assert len(result.stdout) > 0

    def test_all_global_options_available(self):
        """Verify all global options are available."""
        result = run_command(["--help"])

        assert result.returncode == 0
        # Check for documented global options
        help_text = result.stdout.lower()
        assert "--help" in help_text or "-h" in help_text
        assert "--version" in help_text or "-v" in help_text
