"""Format detection and parsing for specifications."""

import json
import re
from pathlib import Path
from typing import Any

import yaml

from specnut.models import FormatEnum


def detect_format(file_path: Path) -> FormatEnum:
    """Detect format from file extension.

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


def parse_yaml(content: str) -> dict[str, Any]:
    """Parse YAML content.

    Args:
        content: YAML content as string

    Returns:
        Parsed data as dictionary

    Raises:
        ValueError: If YAML is invalid
    """
    try:
        data = yaml.safe_load(content)
        if data is None:
            return {}
        if not isinstance(data, dict):
            # Wrap non-dict YAML in a dict
            return {"content": data}
        return data
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}") from e


def parse_json(content: str) -> dict[str, Any]:
    """Parse JSON content.

    Args:
        content: JSON content as string

    Returns:
        Parsed data as dictionary

    Raises:
        ValueError: If JSON is invalid
    """
    try:
        data = json.loads(content)
        if not isinstance(data, dict):
            # Wrap non-dict JSON in a dict
            return {"content": data}
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e


def normalize_section_name(name: str) -> str:
    """Normalize section name by removing markdown formatting.

    Strips patterns like *(mandatory)*, *(optional)*, etc.

    Args:
        name: Raw section name from markdown header

    Returns:
        Normalized section name
    """
    # Remove markdown emphasis patterns like *(mandatory)*, *(optional)*
    normalized = re.sub(r"\s*\*\([^)]+\)\*?\s*$", "", name)
    return normalized.strip()


def parse_markdown(content: str) -> dict[str, Any]:
    """Parse Markdown content into sections.

    This is a basic parser that extracts sections based on headers.

    Args:
        content: Markdown content as string

    Returns:
        Dictionary with sections

    Structure:
        {
            "title": "Document title",
            "sections": {
                "Section Name": "section content",
                ...
            },
            "raw": "original content"
        }
    """
    lines = content.split("\n")
    sections: dict[str, str] = {}
    current_section = "preamble"
    current_content: list[str] = []
    title = ""

    for line in lines:
        # Check for headers
        if line.startswith("# "):
            # H1 - Document title
            if not title:
                title = line[2:].strip()
            else:
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = normalize_section_name(line[2:].strip())
                current_content = []
        elif line.startswith("## "):
            # H2 - Section
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = normalize_section_name(line[3:].strip())
            current_content = []
        elif line.startswith("### "):
            # H3 - Subsection
            current_content.append(line)
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return {
        "title": title or "Untitled",
        "sections": sections,
        "raw": content,
    }


def parse_content(content: str, format: FormatEnum) -> dict[str, Any]:
    """Parse content based on format.

    Args:
        content: Content to parse
        format: Format of the content

    Returns:
        Parsed data as dictionary

    Raises:
        ValueError: If parsing fails
    """
    if format == FormatEnum.YAML:
        return parse_yaml(content)
    elif format == FormatEnum.JSON:
        return parse_json(content)
    elif format == FormatEnum.MARKDOWN:
        return parse_markdown(content)
    else:
        raise ValueError(f"Unsupported format for parsing: {format}")


def serialize_yaml(data: dict[str, Any]) -> str:
    """Serialize data to YAML.

    Args:
        data: Data to serialize

    Returns:
        YAML string
    """
    return yaml.dump(data, default_flow_style=False, allow_unicode=True)


def serialize_json(data: dict[str, Any]) -> str:
    """Serialize data to JSON.

    Args:
        data: Data to serialize

    Returns:
        JSON string
    """
    return json.dumps(data, indent=2, ensure_ascii=False)


def serialize_markdown(data: dict[str, Any]) -> str:
    """Serialize data to Markdown.

    Args:
        data: Data with title and sections

    Returns:
        Markdown string
    """
    if "raw" in data:
        return data["raw"]

    lines = []

    # Title
    if "title" in data:
        lines.append(f"# {data['title']}")
        lines.append("")

    # Sections
    if "sections" in data:
        for section_name, section_content in data["sections"].items():
            if section_name != "preamble":
                lines.append(f"## {section_name}")
                lines.append("")
            lines.append(section_content)
            lines.append("")

    return "\n".join(lines)


def serialize_content(data: dict[str, Any], format: FormatEnum) -> str:
    """Serialize data to specified format.

    Args:
        data: Data to serialize
        format: Target format

    Returns:
        Serialized string

    Raises:
        ValueError: If format is unsupported
    """
    if format == FormatEnum.YAML:
        return serialize_yaml(data)
    elif format == FormatEnum.JSON:
        return serialize_json(data)
    elif format == FormatEnum.MARKDOWN:
        return serialize_markdown(data)
    elif format == FormatEnum.COMPACT:
        # Compact format is just compressed markdown
        return serialize_markdown(data)
    else:
        raise ValueError(f"Unsupported format for serialization: {format}")
