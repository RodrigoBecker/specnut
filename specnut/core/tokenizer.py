"""Token counting functionality using tiktoken."""

import tiktoken


# Default encoding for GPT-4 and GPT-3.5-turbo
DEFAULT_ENCODING = "cl100k_base"


def get_encoding(encoding_name: str = DEFAULT_ENCODING) -> tiktoken.Encoding:
    """Get tiktoken encoding.

    Args:
        encoding_name: Name of the encoding (default: cl100k_base)

    Returns:
        tiktoken Encoding object

    Raises:
        ValueError: If encoding name is invalid
    """
    try:
        return tiktoken.get_encoding(encoding_name)
    except Exception as e:
        raise ValueError(f"Invalid encoding '{encoding_name}': {e}") from e


def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for
        encoding_name: Name of the encoding (default: cl100k_base)

    Returns:
        Number of tokens

    Raises:
        ValueError: If encoding fails
    """
    if not text:
        return 0

    try:
        encoding = get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        raise ValueError(f"Failed to count tokens: {e}") from e


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count without using tiktoken.

    This is a fallback when tiktoken is not available.
    Estimates ~1 token per 4 characters (conservative).

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated number of tokens
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def calculate_compression_ratio(original_tokens: int, compressed_tokens: int) -> float:
    """Calculate compression ratio.

    Args:
        original_tokens: Token count before compression
        compressed_tokens: Token count after compression

    Returns:
        Compression ratio (0.0 to 1.0)

    Raises:
        ValueError: If token counts are invalid
    """
    if original_tokens <= 0:
        raise ValueError(f"Original tokens must be positive, got {original_tokens}")

    if compressed_tokens < 0:
        raise ValueError(f"Compressed tokens cannot be negative, got {compressed_tokens}")

    if compressed_tokens > original_tokens:
        raise ValueError(
            f"Compressed tokens ({compressed_tokens}) cannot exceed "
            f"original tokens ({original_tokens})"
        )

    if original_tokens == 0:
        return 0.0

    return (original_tokens - compressed_tokens) / original_tokens
