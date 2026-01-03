"""
Speckit integration for automatic digest generation.

This module provides optional integration with Speckit when both tools are installed.
It enables automatic digest generation as part of Speckit workflows.
"""

import importlib.util
import os
from pathlib import Path
from typing import Optional

import yaml


# Detect if Speckit is available
def is_speckit_available() -> bool:
    """Check if Speckit is installed and available."""
    spec = importlib.util.find_spec("speckit")
    return spec is not None


SPECKIT_AVAILABLE = is_speckit_available()


def load_config(config_path: Optional[Path] = None) -> dict:
    """
    Load SpecNut configuration from .specnut.yaml.

    Args:
        config_path: Path to config file. If None, searches in current dir and home.

    Returns:
        Configuration dictionary.
    """
    if config_path is None:
        # Search for config in standard locations
        search_paths = [
            Path.cwd() / ".specnut.yaml",
            Path.cwd() / ".specnut.yml",
            Path.home() / ".config" / "specnut" / "config.yaml",
        ]

        for path in search_paths:
            if path.exists():
                config_path = path
                break

    if config_path and config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}

    return {}


def is_auto_optimize_enabled() -> bool:
    """
    Check if auto-optimization is enabled via config or environment variable.

    Returns:
        True if auto-optimization is enabled.
    """
    # Check environment variable first
    env_var = os.environ.get("SPECNUT_AUTO_OPTIMIZE", "").lower()
    if env_var in ("true", "1", "yes"):
        return True
    if env_var in ("false", "0", "no"):
        return False

    # Check config file
    config = load_config()
    return config.get("speckit", {}).get("auto_optimize", False)


def auto_digest(spec_path: Path, output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Automatically generate a digest for a specification file.

    This function is called by Speckit hooks to automatically create
    optimized digests while preserving the original specification.

    Args:
        spec_path: Path to the specification file.
        output_dir: Optional output directory for digest. Defaults to same dir as spec.

    Returns:
        Path to the created digest file, or None if generation failed.
    """
    if not spec_path.exists():
        return None

    # Import here to avoid circular dependencies
    from specnut.core.optimizer import DigestGenerator
    from specnut.models.specification import Specification

    try:
        # Load specification
        spec = Specification.from_file(spec_path)

        # Generate digest
        generator = DigestGenerator()
        digest = generator.generate(spec)

        # Determine output path
        if output_dir is None:
            output_dir = spec_path.parent

        output_path = output_dir / f"{spec_path.stem}.digest{spec_path.suffix}"

        # Write digest (preserves original file)
        digest.to_file(output_path)

        return output_path

    except Exception:
        # Silently fail - don't break Speckit workflow
        return None


def register_hooks() -> None:
    """
    Register SpecNut hooks with Speckit.

    This function registers digest generation hooks that are called
    at appropriate points in the Speckit workflow.
    """
    if not SPECKIT_AVAILABLE:
        return

    try:
        # Import Speckit hook system
        import speckit.hooks  # type: ignore

        # Register before_spec_load hook for auto-digest generation
        if hasattr(speckit.hooks, "register"):
            speckit.hooks.register("before_spec_load", auto_digest)

    except (ImportError, AttributeError):
        # Speckit version doesn't support hooks, or API changed
        pass


def get_digest_directory() -> Path:
    """
    Get the configured digest output directory.

    Returns:
        Path to digest directory from config, or default location.
    """
    config = load_config()
    digest_dir = config.get("speckit", {}).get("digest_directory", ".specify/digests")

    return Path(digest_dir)


# Auto-register hooks if Speckit is available and auto-optimize is enabled
if SPECKIT_AVAILABLE and is_auto_optimize_enabled():
    register_hooks()
