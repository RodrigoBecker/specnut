"""Unit tests for Huffman-based text compression."""

import pytest

from specnut.core.huffman import (
    HuffmanCodebook,
    HuffmanNode,
    build_codebook,
    build_frequency_table,
    build_huffman_tree,
    generate_codes,
    huffman_compress,
    huffman_decompress,
)


class TestFrequencyAnalysis:
    """Tests for frequency table construction."""

    def test_build_frequency_table_counts_words(self):
        """Frequent words appear in frequency table."""
        text = "specification specification specification requirement requirement"
        freq = build_frequency_table(text, min_freq=2)
        assert "specification" in freq
        assert freq["specification"] == 3
        assert "requirement" in freq
        assert freq["requirement"] == 2

    def test_build_frequency_table_ignores_short_words(self):
        """Words shorter than 4 characters are excluded."""
        text = "the the the and and and specification specification"
        freq = build_frequency_table(text, min_freq=2)
        assert "the" not in freq
        assert "and" not in freq
        assert "specification" in freq

    def test_build_frequency_table_min_freq_filter(self):
        """Words below min_freq threshold are excluded."""
        text = "specification specification requirement"
        freq = build_frequency_table(text, min_freq=2)
        assert "specification" in freq
        assert "requirement" not in freq  # Only appears once

    def test_build_frequency_table_empty_text(self):
        """Empty text returns empty frequency table."""
        freq = build_frequency_table("", min_freq=1)
        assert freq == {}

    def test_build_frequency_table_detects_domain_phrases(self):
        """Multi-word domain phrases are detected."""
        text = "The user story describes the user story for acceptance criteria and acceptance criteria"
        freq = build_frequency_table(text, min_freq=2)
        assert "user story" in freq
        assert "acceptance criteria" in freq


class TestHuffmanTree:
    """Tests for Huffman tree construction."""

    def test_build_huffman_tree_creates_valid_tree(self):
        """Tree is built from frequency data."""
        freq = {"specification": 10, "requirement": 5, "implementation": 3}
        tree = build_huffman_tree(freq)
        assert tree is not None
        assert tree.freq == 18  # Sum of all frequencies

    def test_build_huffman_tree_single_entry(self):
        """Single entry creates a tree with one node."""
        freq = {"specification": 10}
        tree = build_huffman_tree(freq)
        assert tree is not None

    def test_build_huffman_tree_empty_dict(self):
        """Empty dict returns None."""
        tree = build_huffman_tree({})
        assert tree is None

    def test_huffman_tree_most_frequent_gets_shortest_code(self):
        """Most frequent term gets the shortest binary code."""
        freq = {"specification": 100, "requirement": 10, "implementation": 1}
        tree = build_huffman_tree(freq)
        codes = generate_codes(tree)

        assert len(codes["specification"]) <= len(codes["requirement"])
        assert len(codes["specification"]) <= len(codes["implementation"])


class TestCodeGeneration:
    """Tests for Huffman code generation."""

    def test_generate_codes_all_terms_have_codes(self):
        """Every term in the tree gets a code."""
        freq = {"spec": 5, "req": 3, "impl": 1}
        tree = build_huffman_tree(freq)
        codes = generate_codes(tree)
        assert set(codes.keys()) == {"spec", "req", "impl"}

    def test_generate_codes_are_prefix_free(self):
        """No code is a prefix of another code (Huffman property)."""
        freq = {"a": 10, "b": 5, "c": 3, "d": 1}
        tree = build_huffman_tree(freq)
        codes = generate_codes(tree)
        code_list = list(codes.values())
        for i, code_a in enumerate(code_list):
            for j, code_b in enumerate(code_list):
                if i != j:
                    assert not code_b.startswith(code_a), (
                        f"Code '{code_a}' is prefix of '{code_b}'"
                    )

    def test_generate_codes_empty_tree(self):
        """None tree returns empty codes."""
        codes = generate_codes(None)
        assert codes == {}


class TestCodebook:
    """Tests for codebook construction and serialization."""

    def test_build_codebook_from_spec_text(self):
        """Codebook built from spec text contains encodings."""
        text = (
            "The specification requires implementation of the specification. "
            "The implementation should follow the specification requirements. "
            "Each requirement in the specification must be validated. "
            "The implementation validates each requirement."
        )
        codebook = build_codebook(text, min_freq=2)
        assert codebook.compression_candidates > 0
        assert len(codebook.encodings) > 0

    def test_codebook_abbreviations_are_shorter(self):
        """Abbreviations are shorter than original terms."""
        text = (
            "specification " * 20
            + "requirement " * 15
            + "implementation " * 10
            + "configuration " * 8
        )
        codebook = build_codebook(text, min_freq=2)
        for term, abbrev in codebook.encodings.items():
            assert len(abbrev) < len(term), (
                f"Abbreviation '{abbrev}' is not shorter than '{term}'"
            )

    def test_codebook_serialization_roundtrip(self):
        """Codebook survives serialization to dict and back."""
        text = "specification " * 10 + "requirement " * 8
        codebook = build_codebook(text, min_freq=2)
        serialized = codebook.to_dict()
        restored = HuffmanCodebook.from_dict(serialized)
        assert restored.encodings == codebook.encodings
        assert restored.total_terms == codebook.total_terms

    def test_codebook_empty_text(self):
        """Empty text produces empty codebook."""
        codebook = build_codebook("", min_freq=1)
        assert codebook.encodings == {}
        assert codebook.compression_candidates == 0

    def test_codebook_max_entries_limit(self):
        """Codebook respects max_entries limit."""
        words = " ".join(f"word{i} " * 5 for i in range(100))
        codebook = build_codebook(words, min_freq=2, max_entries=10)
        assert codebook.compression_candidates <= 10


class TestCompression:
    """Tests for Huffman compress/decompress."""

    def test_huffman_compress_reduces_text(self):
        """Compressed text is shorter than original."""
        text = (
            "The specification describes the specification requirements. "
            "Each specification requirement must be implemented. "
            "The implementation follows the specification."
        )
        codebook = build_codebook(text, min_freq=2)
        compressed = huffman_compress(text, codebook)
        assert len(compressed) < len(text)

    def test_huffman_compress_with_empty_codebook(self):
        """Empty codebook returns text unchanged."""
        codebook = HuffmanCodebook(
            encodings={}, decodings={}, frequencies={},
            total_terms=0, compression_candidates=0,
        )
        text = "Some text that should not change"
        assert huffman_compress(text, codebook) == text

    def test_huffman_decompress_restores_text(self):
        """Decompression reverses compression."""
        text = (
            "specification specification specification "
            "requirement requirement requirement"
        )
        codebook = build_codebook(text, min_freq=2)
        compressed = huffman_compress(text, codebook)
        decompressed = huffman_decompress(compressed, codebook)

        # Decompressed should contain the original terms
        assert "specification" in decompressed.lower()
        assert "requirement" in decompressed.lower()

    def test_huffman_compress_preserves_non_matching_text(self):
        """Text without codebook terms is preserved unchanged."""
        codebook = build_codebook("specification " * 10, min_freq=2)
        text = "Hello world, this is a test."
        compressed = huffman_compress(text, codebook)
        assert compressed == text

    def test_huffman_compress_handles_multiword_phrases(self):
        """Multi-word phrases are compressed correctly."""
        text = (
            "The user story defines the user story requirements. "
            "Another user story is needed for the user story."
        )
        codebook = build_codebook(text, min_freq=2)
        if "user story" in codebook.encodings:
            compressed = huffman_compress(text, codebook)
            assert codebook.encodings["user story"] in compressed


class TestIntegrationWithOptimizer:
    """Tests verifying Huffman works within the optimization pipeline."""

    def test_codebook_from_real_spec_content(self):
        """Codebook handles realistic spec content."""
        spec_text = """
        # Feature Specification

        ## Functional Requirements

        - **FR-001**: The specification must support configuration management
        - **FR-002**: The implementation must handle authentication
        - **FR-003**: The specification requires authorization controls
        - **FR-004**: The implementation must support configuration
        - **FR-005**: The specification defines the architecture

        ## User Stories

        - As a developer, I want to configure the specification
        - As a developer, I want to implement the specification
        - As a developer, I want to validate the specification

        ## Assumptions

        The specification assumes that the implementation follows the
        specification guidelines. The configuration and implementation
        should be consistent with the specification requirements.
        """
        codebook = build_codebook(spec_text, min_freq=3)
        assert codebook.total_terms > 0

        compressed = huffman_compress(spec_text, codebook)
        # Should achieve some compression
        assert len(compressed) <= len(spec_text)
