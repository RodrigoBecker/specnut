"""Digest generation and compression logic."""

import re
from datetime import datetime
from typing import Any

from specnut import __version__
from specnut.core.parser import parse_content, serialize_content
from specnut.core.tokenizer import calculate_compression_ratio, count_tokens
from specnut.models import FormatEnum, Priority
from specnut.models.digest import Digest, DigestMetadata
from specnut.models.metrics import SectionMetrics, TokenMetrics
from specnut.models.optimization import OptimizationProfile
from specnut.models.specification import Specification


def compress_text(
    text: str, priority: Priority, abbreviations: dict[str, str] | None = None
) -> str:
    """Compress text based on priority level.

    Args:
        text: Text to compress
        priority: Compression priority level
        abbreviations: Optional abbreviation map

    Returns:
        Compressed text
    """
    if not text:
        return text

    compressed = text

    if priority == Priority.CRITICAL:
        # Preserve 100% - minimal compression (just whitespace)
        compressed = re.sub(r"\n\n+", "\n\n", compressed)
        compressed = re.sub(r"  +", " ", compressed)
        return compressed.strip()

    if priority == Priority.HIGH:
        # Summarize - apply abbreviations and remove verbose content
        # Remove meta-commentary sections and non-critical subsections
        meta_patterns = [
            r"\*\*Why this priority\*\*:.*?(?=\n\n|\n\*\*|$)",
            r"\*\*Independent Test\*\*:.*?(?=\n\n|\n\*\*|$)",
            r"\*\*Rationale\*\*:.*?(?=\n\n|\n\*\*|$)",
            r"\*\*Note\*\*:.*?(?=\n\n|\n\*\*|$)",
            # Remove Edge Cases subsection (can be inferred from requirements)
            r"###?\s*Edge Cases.*?(?=\n###|\n##|$)",
            # Remove Assumptions subsection
            r"###?\s*Assumptions.*?(?=\n###|\n##|$)",
        ]
        for pattern in meta_patterns:
            compressed = re.sub(pattern, "", compressed, flags=re.DOTALL)

        # Apply abbreviations first
        if abbreviations:
            for full, abbrev in abbreviations.items():
                compressed = re.sub(
                    r"\b" + re.escape(full) + r"\b", abbrev, compressed, flags=re.IGNORECASE
                )

        # Contract verbose phrases to shorter equivalents
        contractions = [
            (r"\bA (developer|user|person|team member) wants to\b", r"\1:"),
            (r"\bThe (system|tool|CLI|application) (MUST|SHOULD|MAY|CAN)\b", r"\2"),
            (r"\b(so that|so they can|in order to)\b", r"to"),
            (r"\b(is able to|are able to)\b", r"can"),
            (r"\b(will be able to)\b", r"can"),
            (r"\b(has the ability to)\b", r"can"),
            (r"\bwithout manual setup each time\b", r""),
            (r"\bacross multiple projects\b", r"globally"),
            (r"\bthe latest version\b", r"latest"),
            (r"\bAcceptance Scenarios\b", r"Acceptance"),
            (r"\(Priority:\s*P\d+\)", r""),  # Remove priority labels
            (r"\bUser Story\b", r"US"),
            (r"\bFunctional Requirements\b", r"Requirements"),  # Shorten header
            (r"\bcommand-line\b", r"CLI"),
            (r"\bvia\b", r"w/"),
            (r"\bprovide\b", r"give"),
            (r"\binformation\b", r"info"),
        ]
        for pattern, replacement in contractions:
            compressed = re.sub(pattern, replacement, compressed, flags=re.IGNORECASE)

        # Remove filler words and verbose phrases
        filler_words = [
            r"\b(basically|essentially|actually|literally|really|very|quite|rather|somewhat)\b",
            r"\b(in order to|in terms of|with regard to|with respect to)\b",
            r"\b(it is important to note that|it should be noted that|please note that)\b",
            r"\b(in other words|that is to say|as a matter of fact)\b",
            r"\b(for example|for instance|such as)\b",
        ]
        for pattern in filler_words:
            compressed = re.sub(pattern, "", compressed, flags=re.IGNORECASE)

        # Remove unnecessary articles where context is clear
        compressed = re.sub(
            r"\b(a|an|the)\s+(specification|file|command|tool|system|user|developer|digest|version|output|input|flag)\b",
            r"\2",
            compressed,
            flags=re.IGNORECASE,
        )

        # Remove redundant words
        compressed = re.sub(r"\bfile path\b", r"path", compressed, flags=re.IGNORECASE)
        compressed = re.sub(r"\bfile name\b", r"name", compressed, flags=re.IGNORECASE)

        # Remove markdown formatting (but keep structure for important items)
        compressed = re.sub(r"\*\*([^*]+)\*\*", r"\1", compressed)  # Remove bold
        compressed = re.sub(r"_([^_]+)_", r"\1", compressed)  # Remove italics

        # Simplify list formatting
        compressed = re.sub(r"^\s*[\d]+\.\s+", "• ", compressed, flags=re.MULTILINE)

        # Remove horizontal rules (--- separators)
        compressed = re.sub(r"^\s*---+\s*$", "", compressed, flags=re.MULTILINE)

        # Remove subsection headers (### User Story 1)
        compressed = re.sub(r"^###\s+", "", compressed, flags=re.MULTILINE)

        # Remove redundant subsection labels
        compressed = re.sub(
            r"^(Functional|Non-Functional|Technical)\s+(Requirements|Constraints):?\s*$",
            "",
            compressed,
            flags=re.MULTILINE,
        )

        # Remove excessive whitespace
        compressed = re.sub(r"\n\n+", "\n", compressed)
        compressed = re.sub(r"  +", " ", compressed)

    if priority == Priority.MEDIUM:
        # Compress - aggressive abbreviation and simplification
        # Apply abbreviations
        if abbreviations:
            for full, abbrev in abbreviations.items():
                compressed = re.sub(
                    r"\b" + re.escape(full) + r"\b", abbrev, compressed, flags=re.IGNORECASE
                )

        # Remove all verbose phrases and filler
        verbose_patterns = [
            r"\b(basically|essentially|actually|literally|really|very|quite|rather|somewhat)\b",
            r"\b(in order to|in terms of|with regard to|with respect to)\b",
            r"\b(it is important to note that|it should be noted that|please note that)\b",
            r"\b(in other words|that is to say|as a matter of fact)\b",
            r"\b(for example|for instance|such as|including but not limited to)\b",
        ]
        for pattern in verbose_patterns:
            compressed = re.sub(pattern, "", compressed, flags=re.IGNORECASE)

        # Remove all markdown formatting
        compressed = re.sub(r"\*\*([^*]+)\*\*", r"\1", compressed)  # Remove bold
        compressed = re.sub(r"_([^_]+)_", r"\1", compressed)  # Remove italics
        compressed = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", compressed)  # Remove links, keep text

        # Simplify lists - remove all list markers
        compressed = re.sub(r"^\s*[\d\-\*]+\.\s+", "", compressed, flags=re.MULTILINE)

        # Remove section headers (###, ##, etc) - keep just the text
        compressed = re.sub(r"^#+\s+", "", compressed, flags=re.MULTILINE)

        # Remove excessive whitespace and blank lines
        compressed = re.sub(r"\n\n+", "\n", compressed)
        compressed = re.sub(r"  +", " ", compressed)

    if priority == Priority.LOW:
        # Omit - can be removed entirely
        compressed = ""

    return compressed.strip()


def optimize_section(
    section_name: str,
    section_content: str,
    profile: OptimizationProfile,
) -> tuple[str, str]:
    """Optimize a single section.

    Args:
        section_name: Name of the section
        section_content: Content of the section
        profile: Optimization profile to use

    Returns:
        Tuple of (optimized_content, action_taken)
    """
    if not section_content:
        return "", "omitted"

    # Determine priority for this section
    priority = profile.section_priorities.get(section_name, Priority.MEDIUM)

    # Mark protected patterns with placeholders (use format unlikely to be modified by compression)
    protected_patterns: dict[str, str] = {}
    working_content = section_content
    placeholder_counter = 0

    for rule in profile.preserve_rules:
        if rule.action == "preserve":
            # Find all matches and replace with placeholders
            matches = list(re.finditer(rule.pattern, working_content, re.MULTILINE))
            for match in reversed(matches):  # Reverse to maintain positions
                # Use XPRESERVEX format to avoid conflicts with markdown/compression patterns
                placeholder = f"XPRESERVE{placeholder_counter:04d}X"
                protected_patterns[placeholder] = match.group(0)
                working_content = (
                    working_content[: match.start()] + placeholder + working_content[match.end() :]
                )
                placeholder_counter += 1

    # Compress the working content
    optimized = compress_text(working_content, priority, profile.abbreviation_map)

    # Restore protected patterns
    for placeholder, original in protected_patterns.items():
        optimized = optimized.replace(placeholder, original)

    # Determine action taken
    if priority == Priority.CRITICAL or optimized == section_content:
        action = "preserved"
    elif priority == Priority.HIGH:
        action = "summarized"
    elif priority == Priority.MEDIUM:
        action = "compressed"
    else:
        action = "omitted"

    return optimized, action


def generate_digest(
    specification: Specification,
    profile: OptimizationProfile,
    output_format: FormatEnum | None = None,
) -> tuple[Digest, TokenMetrics]:
    """Generate optimized digest from specification.

    Args:
        specification: Specification to optimize
        profile: Optimization profile to use
        output_format: Desired output format (defaults to same as input)

    Returns:
        Tuple of (Digest, TokenMetrics)

    Raises:
        ValueError: If optimization fails
    """
    start_time = datetime.now()

    # Parse content
    parsed_data = parse_content(specification.content, specification.format)

    # Track sections
    sections_compressed: list[str] = []
    sections_preserved: list[str] = []
    sections_breakdown: dict[str, SectionMetrics] = {}

    # Optimize based on format
    if specification.format == FormatEnum.MARKDOWN:
        optimized_data = optimize_markdown(parsed_data, profile, sections_breakdown)
    elif specification.format in (FormatEnum.YAML, FormatEnum.JSON):
        optimized_data = optimize_structured(parsed_data, profile, sections_breakdown)
    else:
        raise ValueError(f"Unsupported format for optimization: {specification.format}")

    # Determine output format
    if output_format is None:
        output_format = specification.format

    # Serialize optimized data
    optimized_content = serialize_content(optimized_data, output_format)

    # Count tokens
    optimized_tokens = count_tokens(optimized_content)

    # Calculate compression ratio
    compression_ratio = calculate_compression_ratio(specification.token_count, optimized_tokens)

    # Build section lists
    for section_name, metrics in sections_breakdown.items():
        if metrics.action_taken in ("preserved"):
            sections_preserved.append(section_name)
        else:
            sections_compressed.append(section_name)

    # Create metadata
    metadata = DigestMetadata(
        source_hash=specification.hash,
        format_version="1.0",
        optimization_profile=profile.name,
        sections_compressed=sections_compressed,
        sections_preserved=sections_preserved,
        generator_version=__version__,
        timestamp=datetime.now(),
    )

    # Create digest
    digest = Digest(
        content=optimized_content,
        format=output_format,
        token_count=optimized_tokens,
        compression_ratio=compression_ratio,
        metadata=metadata,
        source_spec=specification,
    )

    # Calculate processing time
    end_time = datetime.now()
    processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

    # Create metrics
    metrics = TokenMetrics(
        original_tokens=specification.token_count,
        digest_tokens=optimized_tokens,
        percent_saved=compression_ratio,
        processing_time_ms=processing_time_ms,
        timestamp=end_time,
        source_file=str(specification.file_path),
        sections_breakdown=sections_breakdown,
    )

    return digest, metrics


def optimize_markdown(
    parsed_data: dict[str, Any],
    profile: OptimizationProfile,
    sections_breakdown: dict[str, SectionMetrics],
) -> dict[str, Any]:
    """Optimize markdown content.

    Args:
        parsed_data: Parsed markdown data
        profile: Optimization profile
        sections_breakdown: Dictionary to populate with metrics

    Returns:
        Optimized data
    """
    optimized_sections: dict[str, str] = {}

    sections = parsed_data.get("sections", {})

    for section_name, section_content in sections.items():
        original_tokens = count_tokens(section_content)

        optimized_content, action = optimize_section(section_name, section_content, profile)

        optimized_tokens = count_tokens(optimized_content)

        if optimized_content:  # Only include non-empty sections
            optimized_sections[section_name] = optimized_content

        # Track metrics
        if original_tokens > 0:
            reduction = calculate_compression_ratio(original_tokens, optimized_tokens)
            sections_breakdown[section_name] = SectionMetrics(
                section_name=section_name,
                original_tokens=original_tokens,
                digest_tokens=optimized_tokens,
                reduction_percent=reduction,
                action_taken=action,
            )

    return {
        "title": parsed_data.get("title", ""),
        "sections": optimized_sections,
    }


def optimize_structured(
    parsed_data: dict[str, Any],
    profile: OptimizationProfile,
    sections_breakdown: dict[str, SectionMetrics],
) -> dict[str, Any]:
    """Optimize structured data (YAML/JSON).

    Args:
        parsed_data: Parsed structured data
        profile: Optimization profile
        sections_breakdown: Dictionary to populate with metrics

    Returns:
        Optimized data
    """
    optimized: dict[str, Any] = {}

    for key, value in parsed_data.items():
        if isinstance(value, str):
            original_tokens = count_tokens(value)
            optimized_value, action = optimize_section(key, value, profile)
            optimized_tokens = count_tokens(optimized_value)

            if optimized_value:
                optimized[key] = optimized_value

            if original_tokens > 0:
                reduction = calculate_compression_ratio(original_tokens, optimized_tokens)
                sections_breakdown[key] = SectionMetrics(
                    section_name=key,
                    original_tokens=original_tokens,
                    digest_tokens=optimized_tokens,
                    reduction_percent=reduction,
                    action_taken=action,
                )
        elif isinstance(value, dict):
            # Recursively optimize nested dictionaries
            optimized[key] = optimize_structured(value, profile, sections_breakdown)
        elif isinstance(value, list):
            # Preserve lists (may contain important structured data)
            optimized[key] = value
        else:
            # Preserve other types
            optimized[key] = value

    return optimized
