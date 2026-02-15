"""Huffman-based text compression for specification optimization.

Implements a semantic Huffman strategy where frequently occurring words and
phrases in specification text are replaced with shorter abbreviated tokens.
Unlike binary Huffman coding, this produces human-readable compressed text
that reduces token consumption for AI agents.

The algorithm:
1. Analyze word/phrase frequency across the spec
2. Build a Huffman tree from frequencies
3. Map frequent terms to short abbreviation codes
4. Replace terms in text with their abbreviated forms
5. Store the codebook for decompression/reference
"""

from __future__ import annotations

import heapq
import re
from collections import Counter
from dataclasses import dataclass, field


# Domain-specific phrases that appear frequently in specs.
# These are pre-seeded as high-value compression targets.
SPEC_DOMAIN_PHRASES: list[str] = [
    "specification",
    "requirement",
    "implementation",
    "configuration",
    "application",
    "architecture",
    "authentication",
    "authorization",
    "functionality",
    "documentation",
    "microservices",
    "distributed",
    "infrastructure",
    "optimization",
    "performance",
    "integration",
    "deployment",
    "environment",
    "development",
    "maintenance",
    "dependency",
    "dependencies",
    "compression",
    "processing",
    "validation",
    "notification",
    "description",
    "acceptance criteria",
    "user story",
    "functional requirement",
    "non-functional requirement",
    "success criteria",
    "edge case",
    "use case",
]


@dataclass(order=True)
class HuffmanNode:
    """Node in a Huffman tree.

    Attributes:
        freq: Frequency count for this node
        term: The word/phrase (leaf nodes only)
        left: Left child
        right: Right child
    """

    freq: int
    term: str = field(default="", compare=False)
    left: HuffmanNode | None = field(default=None, compare=False, repr=False)
    right: HuffmanNode | None = field(default=None, compare=False, repr=False)

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


def _tokenize_for_frequency(text: str) -> list[str]:
    """Split text into words for frequency analysis.

    Extracts words, preserving common multi-word spec phrases.

    Args:
        text: Input text

    Returns:
        List of words/phrases
    """
    lower = text.lower()
    tokens: list[str] = []

    # First extract multi-word domain phrases
    for phrase in sorted(SPEC_DOMAIN_PHRASES, key=len, reverse=True):
        if " " in phrase and phrase in lower:
            count = lower.count(phrase)
            tokens.extend([phrase] * count)

    # Then extract single words (4+ chars to avoid compressing tiny words)
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
    tokens.extend(w.lower() for w in words)

    return tokens


def build_frequency_table(text: str, min_freq: int = 2) -> dict[str, int]:
    """Build word/phrase frequency table from specification text.

    Args:
        text: Specification text to analyze
        min_freq: Minimum occurrences to include (default: 2)

    Returns:
        Dictionary mapping terms to their frequency counts
    """
    tokens = _tokenize_for_frequency(text)
    freq = Counter(tokens)
    return {term: count for term, count in freq.items() if count >= min_freq}


def build_huffman_tree(frequencies: dict[str, int]) -> HuffmanNode | None:
    """Build a Huffman tree from frequency table.

    Args:
        frequencies: Term → frequency mapping

    Returns:
        Root node of the Huffman tree, or None if empty
    """
    if not frequencies:
        return None

    heap: list[HuffmanNode] = [
        HuffmanNode(freq=freq, term=term) for term, freq in frequencies.items()
    ]
    heapq.heapify(heap)

    if len(heap) == 1:
        node = heapq.heappop(heap)
        return HuffmanNode(freq=node.freq, left=node)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, merged)

    return heap[0] if heap else None


def generate_codes(root: HuffmanNode | None) -> dict[str, str]:
    """Generate Huffman binary codes from tree.

    Args:
        root: Root of the Huffman tree

    Returns:
        Dictionary mapping terms to their binary code strings
    """
    if root is None:
        return {}

    codes: dict[str, str] = {}

    def _traverse(node: HuffmanNode, code: str) -> None:
        if node.is_leaf and node.term:
            codes[node.term] = code or "0"
            return
        if node.left:
            _traverse(node.left, code + "0")
        if node.right:
            _traverse(node.right, code + "1")

    _traverse(root, "")
    return codes


def _code_to_abbreviation(term: str, binary_code: str) -> str:
    """Convert a Huffman binary code into a readable short abbreviation.

    Instead of using raw binary codes, we generate human-readable abbreviations
    based on the code length (shorter code = shorter abbreviation).

    Strategy:
    - Very frequent (code len 1-3): First 2 chars + number
    - Frequent (code len 4-6): First 3 chars
    - Less frequent (code len 7+): First 4 chars

    Args:
        term: The original term
        binary_code: The Huffman binary code

    Returns:
        Short readable abbreviation
    """
    clean = term.replace(" ", "")
    code_len = len(binary_code)

    if code_len <= 3:
        abbrev = clean[:2].upper()
    elif code_len <= 6:
        abbrev = clean[:3].upper()
    else:
        abbrev = clean[:4].upper()

    return abbrev


@dataclass
class HuffmanCodebook:
    """Stores the encoding/decoding mapping for Huffman compression.

    Attributes:
        encodings: Maps original term → abbreviation
        decodings: Maps abbreviation → original term
        frequencies: Original frequency table
        total_terms: Total terms analyzed
        compression_candidates: Number of terms selected for compression
    """

    encodings: dict[str, str]
    decodings: dict[str, str]
    frequencies: dict[str, int]
    total_terms: int
    compression_candidates: int

    def to_dict(self) -> dict:
        """Serialize codebook for storage in digest metadata."""
        return {
            "encodings": self.encodings,
            "total_terms": self.total_terms,
            "compression_candidates": self.compression_candidates,
        }

    @classmethod
    def from_dict(cls, data: dict) -> HuffmanCodebook:
        """Reconstruct codebook from serialized dict."""
        encodings = data.get("encodings", {})
        decodings = {v: k for k, v in encodings.items()}
        return cls(
            encodings=encodings,
            decodings=decodings,
            frequencies={},
            total_terms=data.get("total_terms", 0),
            compression_candidates=data.get("compression_candidates", 0),
        )


def build_codebook(
    text: str,
    min_freq: int = 2,
    max_entries: int = 50,
) -> HuffmanCodebook:
    """Build a Huffman-based codebook for text compression.

    Analyzes text frequency, builds a Huffman tree, and generates
    short abbreviations for the most frequent terms.

    Args:
        text: Specification text to analyze
        min_freq: Minimum frequency to consider for compression
        max_entries: Maximum number of abbreviation entries

    Returns:
        HuffmanCodebook with encoding/decoding maps
    """
    frequencies = build_frequency_table(text, min_freq=min_freq)

    if not frequencies:
        return HuffmanCodebook(
            encodings={},
            decodings={},
            frequencies={},
            total_terms=0,
            compression_candidates=0,
        )

    # Sort by frequency (descending) and take top entries
    sorted_terms = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
    top_terms = dict(sorted_terms[:max_entries])

    # Build Huffman tree to determine relative code lengths
    tree = build_huffman_tree(top_terms)
    codes = generate_codes(tree)

    # Generate unique abbreviations
    encodings: dict[str, str] = {}
    used_abbrevs: set[str] = set()

    # Process in order of Huffman code length (shortest first = most frequent)
    for term, code in sorted(codes.items(), key=lambda x: len(x[1])):
        # Only compress terms where the abbreviation is meaningfully shorter
        abbrev = _code_to_abbreviation(term, code)

        # Ensure uniqueness by appending a counter if needed
        base_abbrev = abbrev
        counter = 1
        while abbrev in used_abbrevs:
            abbrev = f"{base_abbrev}{counter}"
            counter += 1

        # Only use abbreviation if it actually saves characters
        if len(abbrev) < len(term) - 1:
            encodings[term] = abbrev
            used_abbrevs.add(abbrev)

    decodings = {v: k for k, v in encodings.items()}

    return HuffmanCodebook(
        encodings=encodings,
        decodings=decodings,
        frequencies=frequencies,
        total_terms=len(frequencies),
        compression_candidates=len(encodings),
    )


def huffman_compress(text: str, codebook: HuffmanCodebook) -> str:
    """Apply Huffman-based abbreviation compression to text.

    Replaces frequent terms with their codebook abbreviations.

    Args:
        text: Text to compress
        codebook: Encoding codebook

    Returns:
        Compressed text with abbreviations applied
    """
    if not codebook.encodings:
        return text

    result = text

    # Apply multi-word phrase replacements first (longest first)
    multi_word = {k: v for k, v in codebook.encodings.items() if " " in k}
    for term, abbrev in sorted(multi_word.items(), key=lambda x: len(x[0]), reverse=True):
        result = re.sub(
            re.escape(term),
            abbrev,
            result,
            flags=re.IGNORECASE,
        )

    # Apply single-word replacements (word boundary aware)
    single_word = {k: v for k, v in codebook.encodings.items() if " " not in k}
    for term, abbrev in single_word.items():
        result = re.sub(
            r"\b" + re.escape(term) + r"\b",
            abbrev,
            result,
            flags=re.IGNORECASE,
        )

    return result


def huffman_decompress(text: str, codebook: HuffmanCodebook) -> str:
    """Reverse Huffman compression using codebook.

    Args:
        text: Compressed text
        codebook: Decoding codebook

    Returns:
        Decompressed text with abbreviations expanded
    """
    if not codebook.decodings:
        return text

    result = text

    # Replace abbreviations with original terms (longest abbreviation first)
    for abbrev, term in sorted(
        codebook.decodings.items(), key=lambda x: len(x[0]), reverse=True
    ):
        result = re.sub(
            r"\b" + re.escape(abbrev) + r"\b",
            term,
            result,
        )

    return result
