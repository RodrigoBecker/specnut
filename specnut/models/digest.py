"""Digest model representing optimized specification output."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from specnut.models import FormatEnum

if TYPE_CHECKING:
    from specnut.models.specification import Specification


@dataclass
class DigestMetadata:
    """Metadata about digest generation.

    Attributes:
        source_hash: Hash of original specification
        format_version: Digest format version (e.g., "1.0")
        optimization_profile: Profile used (default/low/medium/high)
        sections_compressed: List of section names that were compressed
        sections_preserved: List of section names preserved intact
        generator_version: SpecNut version that created digest
        timestamp: Generation timestamp
    """

    source_hash: str
    format_version: str
    optimization_profile: str
    sections_compressed: list[str]
    sections_preserved: list[str]
    generator_version: str
    timestamp: datetime


@dataclass(frozen=True)
class Digest:
    """Represents an optimized, compressed version of a specification.

    Attributes:
        content: Optimized/compressed content
        format: Output format (YAML/JSON/MARKDOWN/COMPACT)
        token_count: Number of tokens in digest
        compression_ratio: Percentage of tokens saved (0.0 to 1.0)
        metadata: Metadata about digest generation
        source_spec: Reference to original specification
        created_at: When digest was generated
    """

    content: str
    format: FormatEnum
    token_count: int
    compression_ratio: float
    metadata: DigestMetadata
    source_spec: "Specification"
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate digest after initialization."""
        if not self.content:
            raise ValueError("Digest content must not be empty")

        if self.token_count <= 0:
            raise ValueError(f"Token count must be positive, got {self.token_count}")

        if self.token_count >= self.source_spec.token_count:
            raise ValueError(
                f"Digest token count ({self.token_count}) must be less than "
                f"source token count ({self.source_spec.token_count})"
            )

        if self.compression_ratio < 0.0 or self.compression_ratio > 1.0:
            raise ValueError(
                f"Compression ratio must be between 0.0 and 1.0, got {self.compression_ratio}"
            )

    def to_file(self, output_path: Path) -> None:
        """Write digest to disk with embedded metadata.

        Args:
            output_path: Path where digest should be written

        Raises:
            PermissionError: If output path is not writable
            IOError: If write operation fails
        """
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare metadata dict
            metadata_dict = {
                "source_hash": self.metadata.source_hash,
                "format_version": self.metadata.format_version,
                "optimization_profile": self.metadata.optimization_profile,
                "sections_compressed": self.metadata.sections_compressed,
                "sections_preserved": self.metadata.sections_preserved,
                "generator_version": self.metadata.generator_version,
                "timestamp": self.metadata.timestamp.isoformat(),
                "original_tokens": self.source_spec.token_count,
                "digest_tokens": self.token_count,
                "compression_ratio": self.compression_ratio,
                "source_file": str(self.source_spec.file_path) if self.source_spec else None,
            }

            # Write with format-specific metadata embedding
            if self.format == FormatEnum.MARKDOWN:
                # Use YAML frontmatter for markdown
                frontmatter = "---\n" + yaml.dump({"digest_metadata": metadata_dict}) + "---\n\n"
                full_content = frontmatter + self.content
                output_path.write_text(full_content, encoding="utf-8")
            elif self.format in (FormatEnum.YAML, FormatEnum.JSON):
                # Embed metadata in the structure
                content_dict = (
                    yaml.safe_load(self.content)
                    if self.format == FormatEnum.YAML
                    else json.loads(self.content)
                )
                content_dict["_digest_metadata"] = metadata_dict

                if self.format == FormatEnum.YAML:
                    full_content = yaml.dump(content_dict, default_flow_style=False)
                else:
                    full_content = json.dumps(content_dict, indent=2)

                output_path.write_text(full_content, encoding="utf-8")
            else:
                # For other formats, just write content
                output_path.write_text(self.content, encoding="utf-8")
        except PermissionError as e:
            raise PermissionError(f"Cannot write to {output_path}: {e}") from e
        except Exception as e:
            raise IOError(f"Failed to write digest to {output_path}: {e}") from e

    @classmethod
    def from_file(cls, file_path: Path) -> "Digest":
        """Load digest from file.

        Args:
            file_path: Path to digest file

        Returns:
            Digest object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid digest
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Digest file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")

        # Try to extract metadata based on format
        metadata_dict = None
        digest_content = content

        # Check for YAML frontmatter (markdown)
        if content.startswith("---\n"):
            try:
                parts = content.split("---\n", 2)
                if len(parts) >= 3:
                    frontmatter_data = yaml.safe_load(parts[1])
                    if "digest_metadata" in frontmatter_data:
                        metadata_dict = frontmatter_data["digest_metadata"]
                        digest_content = parts[2].strip()
            except Exception:
                pass

        # Check for embedded metadata in YAML/JSON
        if metadata_dict is None:
            try:
                # Try JSON first
                data = json.loads(content)
                if "_digest_metadata" in data:
                    metadata_dict = data.pop("_digest_metadata")
                    digest_content = json.dumps(data, indent=2)
            except Exception:
                try:
                    # Try YAML
                    data = yaml.safe_load(content)
                    if isinstance(data, dict) and "_digest_metadata" in data:
                        metadata_dict = data.pop("_digest_metadata")
                        digest_content = yaml.dump(data, default_flow_style=False)
                except Exception:
                    pass

        if metadata_dict is None:
            raise ValueError(
                "File does not contain digest metadata - may not be a valid digest file"
            )

        # Reconstruct metadata
        from specnut.models.specification import Specification

        metadata = DigestMetadata(
            source_hash=metadata_dict["source_hash"],
            format_version=metadata_dict["format_version"],
            optimization_profile=metadata_dict["optimization_profile"],
            sections_compressed=metadata_dict.get("sections_compressed", []),
            sections_preserved=metadata_dict.get("sections_preserved", []),
            generator_version=metadata_dict["generator_version"],
            timestamp=datetime.fromisoformat(metadata_dict["timestamp"]),
        )

        # Create a minimal source spec (we don't have the full original)
        source_file = metadata_dict.get("source_file", "unknown")
        source_tokens = metadata_dict.get("original_tokens", 0)

        # Create a placeholder spec (original content not stored in digest)
        source_spec = Specification(
            content="# Original specification (content not preserved in digest)",
            format=FormatEnum.MARKDOWN,  # Default
            token_count=source_tokens,
            file_path=Path(source_file) if source_file else None,
            file_size_bytes=0,
            hash=metadata_dict["source_hash"],
        )

        # Detect format from file extension
        suffix = file_path.suffix.lower()
        if suffix in [".md", ".markdown"]:
            format_enum = FormatEnum.MARKDOWN
        elif suffix in [".yaml", ".yml"]:
            format_enum = FormatEnum.YAML
        elif suffix == ".json":
            format_enum = FormatEnum.JSON
        else:
            format_enum = FormatEnum.MARKDOWN

        # Count tokens in digest content
        from specnut.core.tokenizer import count_tokens

        digest_tokens = count_tokens(digest_content)

        return cls(
            content=digest_content,
            format=format_enum,
            token_count=digest_tokens,
            compression_ratio=metadata_dict.get("compression_ratio", 0.0),
            metadata=metadata,
            source_spec=source_spec,
        )

    def validate_compression_ratio(self) -> bool:
        """Ensure digest meets minimum 30% reduction requirement.

        Returns:
            True if compression ratio >= 0.30, False otherwise
        """
        return self.compression_ratio >= 0.30

    def calculate_savings(self) -> int:
        """Return absolute token count saved.

        Returns:
            Number of tokens saved
        """
        return self.source_spec.token_count - self.token_count
