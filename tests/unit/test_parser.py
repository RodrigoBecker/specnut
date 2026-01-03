"""Unit tests for parser module."""

import json

import pytest
import yaml

from specnut.core.parser import (
    detect_format,
    normalize_section_name,
    parse_content,
    parse_json,
    parse_markdown,
    parse_yaml,
    serialize_content,
    serialize_json,
    serialize_markdown,
    serialize_yaml,
)
from specnut.models import FormatEnum


class TestDetectFormat:
    """Tests for format detection."""

    def test_detect_yaml_yml(self, tmp_path):
        """Test .yml extension detection."""
        file = tmp_path / "test.yml"
        file.touch()
        assert detect_format(file) == FormatEnum.YAML

    def test_detect_yaml_yaml(self, tmp_path):
        """Test .yaml extension detection."""
        file = tmp_path / "test.yaml"
        file.touch()
        assert detect_format(file) == FormatEnum.YAML

    def test_detect_json(self, tmp_path):
        """Test .json extension detection."""
        file = tmp_path / "test.json"
        file.touch()
        assert detect_format(file) == FormatEnum.JSON

    def test_detect_markdown_md(self, tmp_path):
        """Test .md extension detection."""
        file = tmp_path / "test.md"
        file.touch()
        assert detect_format(file) == FormatEnum.MARKDOWN

    def test_detect_markdown_markdown(self, tmp_path):
        """Test .markdown extension detection."""
        file = tmp_path / "test.markdown"
        file.touch()
        assert detect_format(file) == FormatEnum.MARKDOWN

    def test_detect_unsupported_format(self, tmp_path):
        """Test unsupported format raises ValueError."""
        file = tmp_path / "test.txt"
        file.touch()
        with pytest.raises(ValueError, match="Unsupported format"):
            detect_format(file)


class TestNormalizeSectionName:
    """Tests for section name normalization."""

    def test_normalize_mandatory(self):
        """Test removal of *(mandatory)* suffix."""
        assert normalize_section_name("Requirements *(mandatory)*") == "Requirements"

    def test_normalize_optional(self):
        """Test removal of *(optional)* suffix."""
        assert normalize_section_name("Examples *(optional)*") == "Examples"

    def test_normalize_no_suffix(self):
        """Test section name without suffix remains unchanged."""
        assert normalize_section_name("User Stories") == "User Stories"

    def test_normalize_whitespace(self):
        """Test whitespace handling."""
        assert normalize_section_name("  Requirements *(mandatory)*  ") == "Requirements"


class TestParseYAML:
    """Tests for YAML parsing."""

    def test_parse_valid_yaml_dict(self):
        """Test parsing valid YAML dictionary."""
        content = """
title: Test Spec
description: A test specification
        """
        result = parse_yaml(content)
        assert result["title"] == "Test Spec"
        assert result["description"] == "A test specification"

    def test_parse_empty_yaml(self):
        """Test parsing empty YAML returns empty dict."""
        result = parse_yaml("")
        assert result == {}

    def test_parse_yaml_list_wraps_in_dict(self):
        """Test non-dict YAML gets wrapped in dict."""
        content = """
- item1
- item2
        """
        result = parse_yaml(content)
        assert "content" in result
        assert result["content"] == ["item1", "item2"]

    def test_parse_invalid_yaml(self):
        """Test invalid YAML raises ValueError."""
        content = """
        invalid: [yaml: content
        """
        with pytest.raises(ValueError, match="Invalid YAML"):
            parse_yaml(content)


class TestParseJSON:
    """Tests for JSON parsing."""

    def test_parse_valid_json_dict(self):
        """Test parsing valid JSON dictionary."""
        content = '{"title": "Test Spec", "version": "1.0"}'
        result = parse_json(content)
        assert result["title"] == "Test Spec"
        assert result["version"] == "1.0"

    def test_parse_json_array_wraps_in_dict(self):
        """Test JSON array gets wrapped in dict."""
        content = '["item1", "item2"]'
        result = parse_json(content)
        assert "content" in result
        assert result["content"] == ["item1", "item2"]

    def test_parse_invalid_json(self):
        """Test invalid JSON raises ValueError."""
        content = '{"invalid": json}'
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_json(content)


class TestParseMarkdown:
    """Tests for Markdown parsing."""

    def test_parse_markdown_with_title(self):
        """Test parsing markdown with title."""
        content = """# Feature Title

Some preamble content.

## User Stories

Story content here.
        """
        result = parse_markdown(content)
        assert result["title"] == "Feature Title"
        assert "preamble" in result["sections"]
        assert "User Stories" in result["sections"]

    def test_parse_markdown_sections(self):
        """Test markdown section extraction."""
        content = """# Title

## Section One

Content one.

## Section Two

Content two.
        """
        result = parse_markdown(content)
        sections = result["sections"]
        assert "Section One" in sections
        assert "Section Two" in sections
        assert "Content one." in sections["Section One"]
        assert "Content two." in sections["Section Two"]

    def test_parse_markdown_normalizes_section_names(self):
        """Test section names are normalized."""
        content = """# Title

## Requirements *(mandatory)*

Required content.
        """
        result = parse_markdown(content)
        assert "Requirements" in result["sections"]

    def test_parse_markdown_subsections(self):
        """Test H3 subsections are included in content."""
        content = """# Title

## Main Section

### Subsection

Subsection content.
        """
        result = parse_markdown(content)
        section_content = result["sections"]["Main Section"]
        assert "### Subsection" in section_content
        assert "Subsection content." in section_content

    def test_parse_markdown_no_title(self):
        """Test markdown without title uses 'Untitled'."""
        content = """
## Section One

Content.
        """
        result = parse_markdown(content)
        assert result["title"] == "Untitled"


class TestParseContent:
    """Tests for unified content parsing."""

    def test_parse_yaml_content(self):
        """Test parsing YAML content."""
        content = "title: Test"
        result = parse_content(content, FormatEnum.YAML)
        assert result["title"] == "Test"

    def test_parse_json_content(self):
        """Test parsing JSON content."""
        content = '{"title": "Test"}'
        result = parse_content(content, FormatEnum.JSON)
        assert result["title"] == "Test"

    def test_parse_markdown_content(self):
        """Test parsing Markdown content."""
        content = "# Test Title\n\n## Section\n\nContent."
        result = parse_content(content, FormatEnum.MARKDOWN)
        assert result["title"] == "Test Title"
        assert "Section" in result["sections"]

    def test_parse_unsupported_format(self):
        """Test unsupported format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported format"):
            parse_content("content", FormatEnum.COMPACT)


class TestSerializeYAML:
    """Tests for YAML serialization."""

    def test_serialize_yaml_dict(self):
        """Test serializing dictionary to YAML."""
        data = {"title": "Test", "version": "1.0"}
        result = serialize_yaml(data)
        parsed = yaml.safe_load(result)
        assert parsed["title"] == "Test"
        assert parsed["version"] == "1.0"

    def test_serialize_yaml_unicode(self):
        """Test YAML serialization handles unicode."""
        data = {"title": "Test 测试"}
        result = serialize_yaml(data)
        assert "测试" in result


class TestSerializeJSON:
    """Tests for JSON serialization."""

    def test_serialize_json_dict(self):
        """Test serializing dictionary to JSON."""
        data = {"title": "Test", "count": 42}
        result = serialize_json(data)
        parsed = json.loads(result)
        assert parsed["title"] == "Test"
        assert parsed["count"] == 42

    def test_serialize_json_unicode(self):
        """Test JSON serialization handles unicode."""
        data = {"title": "Test 测试"}
        result = serialize_json(data)
        parsed = json.loads(result)
        assert parsed["title"] == "Test 测试"

    def test_serialize_json_formatting(self):
        """Test JSON is indented."""
        data = {"a": 1, "b": 2}
        result = serialize_json(data)
        assert "\n" in result  # Should have newlines from indentation


class TestSerializeMarkdown:
    """Tests for Markdown serialization."""

    def test_serialize_markdown_with_raw(self):
        """Test serializing markdown with raw content."""
        data = {"raw": "# Title\n\n## Section\n\nContent."}
        result = serialize_markdown(data)
        assert result == data["raw"]

    def test_serialize_markdown_from_sections(self):
        """Test serializing markdown from sections dict."""
        data = {
            "title": "Feature Title",
            "sections": {"Introduction": "Intro content.", "Details": "Detail content."},
        }
        result = serialize_markdown(data)
        assert "# Feature Title" in result
        assert "## Introduction" in result
        assert "Intro content." in result
        assert "## Details" in result
        assert "Detail content." in result

    def test_serialize_markdown_preamble(self):
        """Test preamble section doesn't get header."""
        data = {
            "title": "Title",
            "sections": {"preamble": "Preamble text.", "Section": "Section text."},
        }
        result = serialize_markdown(data)
        assert "## preamble" not in result
        assert "Preamble text." in result
        assert "## Section" in result


class TestSerializeContent:
    """Tests for unified content serialization."""

    def test_serialize_yaml_content(self):
        """Test serializing to YAML format."""
        data = {"title": "Test"}
        result = serialize_content(data, FormatEnum.YAML)
        parsed = yaml.safe_load(result)
        assert parsed["title"] == "Test"

    def test_serialize_json_content(self):
        """Test serializing to JSON format."""
        data = {"title": "Test"}
        result = serialize_content(data, FormatEnum.JSON)
        parsed = json.loads(result)
        assert parsed["title"] == "Test"

    def test_serialize_markdown_content(self):
        """Test serializing to Markdown format."""
        data = {"title": "Test Title", "sections": {"Section": "Content."}}
        result = serialize_content(data, FormatEnum.MARKDOWN)
        assert "# Test Title" in result
        assert "## Section" in result

    def test_serialize_compact_content(self):
        """Test compact format uses markdown serialization."""
        data = {"title": "Test", "sections": {"Section": "Content."}}
        result = serialize_content(data, FormatEnum.COMPACT)
        assert "# Test" in result
