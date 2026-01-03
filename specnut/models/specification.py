"""Specification model representing input files to be optimized."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from specnut.models import FormatEnum


@dataclass(frozen=True)
class Specification:
    """Represents an input specification file to be optimized.

    Attributes:
        file_path: Absolute path to the specification file
        format: Detected or specified format (YAML/JSON/MARKDOWN)
        content: Raw content of the specification file
        token_count: Number of tokens in original content
        hash: SHA-256 hash of content for integrity
        encoding_used: Token encoding used (e.g., "cl100k_base")
        file_size_bytes: Size of file in bytes
        created_at: When this object was created
    """

    file_path: Path
    format: FormatEnum
    content: str
    token_count: int
    hash: str
    encoding_used: str = "cl100k_base"
    file_size_bytes: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate specification after initialization."""
        if self.token_count <= 0:
            raise ValueError(f"Token count must be positive, got {self.token_count}")
        if not self.file_path.exists():
            raise FileNotFoundError(f"Specification file not found: {self.file_path}")
        if not self.content:
            raise ValueError("Content must not be empty")
        if len(self.hash) != 64:
            raise ValueError(f"Hash must be 64 character hex string, got {len(self.hash)}")

    @classmethod
    def from_file(cls, file_path: Path) -> "Specification":
        """Load specification from a file.

        Args:
            file_path: Path to the specification file

        Returns:
            Specification instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If format is unsupported or content is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Detect format from extension
        file_format = cls.detect_format(file_path)

        # Read content
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"File is not UTF-8 encoded: {file_path}") from e

        if not content:
            raise ValueError(f"File is empty: {file_path}")

        # Calculate hash
        content_hash = cls.calculate_hash(content)

        # Get file size
        file_size = file_path.stat().st_size

        # Calculate token count (will be implemented in tokenizer module)
        # For now, we'll import it when available
        try:
            from specnut.core.tokenizer import count_tokens

            token_count = count_tokens(content)
        except ImportError:
            # Fallback: rough estimate (will be replaced)
            token_count = len(content.split())

        return cls(
            file_path=file_path.absolute(),
            format=file_format,
            content=content,
            token_count=token_count,
            hash=content_hash,
            file_size_bytes=file_size,
        )

    @staticmethod
    def detect_format(file_path: Path) -> FormatEnum:
        """Auto-detect format from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Detected format

        Raises:
            ValueError: If format is unsupported
        """
        suffix = file_path.suffix.lower()

        format_map = {
            ".yaml": FormatEnum.YAML,
            ".yml": FormatEnum.YAML,
            ".json": FormatEnum.JSON,
            ".md": FormatEnum.MARKDOWN,
            ".markdown": FormatEnum.MARKDOWN,
        }

        if suffix not in format_map:
            supported = ", ".join(format_map.keys())
            raise ValueError(f"Unsupported format '{suffix}'. Supported formats: {supported}")

        return format_map[suffix]

    def validate(self) -> None:
        """Validate file exists, is readable, and format is supported.

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is not readable
            ValueError: If format is unsupported
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {self.file_path}")

        if not self.file_path.stat().st_mode & 0o444:
            raise PermissionError(f"File is not readable: {self.file_path}")

    @staticmethod
    def calculate_hash(content: str) -> str:
        """Compute SHA-256 hash of content.

        Args:
            content: Content to hash

        Returns:
            64-character hex string
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
