"""Data models and enums for SpecNut."""

from enum import Enum


class FormatEnum(str, Enum):
    """Supported file formats for specifications and digests."""

    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"
    COMPACT = "compact"  # Output-only format


class CompressionLevel(str, Enum):
    """Compression levels for digest generation."""

    LOW = "low"  # Conservative compression (~30-35% reduction)
    MEDIUM = "medium"  # Balanced compression (~40-50% reduction) - DEFAULT
    HIGH = "high"  # Aggressive compression (~55-65% reduction)


class Priority(str, Enum):
    """Priority levels for section preservation during compression."""

    CRITICAL = "critical"  # Preserve 100% (no compression)
    HIGH = "high"  # Summarize (remove verbose explanations)
    MEDIUM = "medium"  # Compress (abbreviate, remove filler)
    LOW = "low"  # Omit (can be removed entirely)


__all__ = [
    "FormatEnum",
    "CompressionLevel",
    "Priority",
]
