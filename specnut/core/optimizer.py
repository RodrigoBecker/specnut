"""Digest generation and compression logic."""

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from specnut import __version__
from specnut.core.huffman import HuffmanCodebook, build_codebook, huffman_compress
from specnut.core.parser import parse_content, serialize_content
from specnut.core.tokenizer import calculate_compression_ratio, count_tokens
from specnut.models import FormatEnum, Priority
from specnut.models.digest import Digest, DigestMetadata
from specnut.models.metrics import (
    DirectoryScanResult,
    FileProcessingResult,
    ProcessingSummary,
    ProcessingStatus,
    SectionMetrics,
    TokenMetrics,
)
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

    Uses a two-pass optimization strategy:
    1. Section-level compression (priority-based regex rules)
    2. Huffman-based abbreviation (frequency analysis across full content)

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

    # Pass 1: Section-level compression (priority-based)
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

    # Pass 2: Huffman-based abbreviation compression
    # Build codebook from the original content for best frequency analysis
    # Use lower min_freq for smaller texts to maximize compression
    token_count = specification.token_count
    min_freq = 2 if token_count < 1000 else 3
    max_entries = 60 if token_count < 1000 else 40

    huffman_codebook = build_codebook(
        specification.content,
        min_freq=min_freq,
        max_entries=max_entries,
    )
    if huffman_codebook.encodings:
        candidate = huffman_compress(optimized_content, huffman_codebook)
        candidate_tokens = count_tokens(candidate)
        pre_huffman_tokens = count_tokens(optimized_content)
        # Only use Huffman result if it actually reduces tokens
        if candidate_tokens < pre_huffman_tokens:
            optimized_content = candidate
        else:
            # Huffman didn't help; clear codebook so metadata stays clean
            huffman_codebook = build_codebook("", min_freq=999)

    # Count tokens
    optimized_tokens = count_tokens(optimized_content)

    # Safety: if optimization increased tokens (possible with format conversion),
    # re-serialize from optimized_data in target format, or fall back to original
    if optimized_tokens >= specification.token_count:
        # Try re-serializing optimized data in original format
        fallback_content = serialize_content(optimized_data, specification.format)
        fallback_tokens = count_tokens(fallback_content)
        if fallback_tokens < specification.token_count:
            optimized_content = fallback_content
            optimized_tokens = fallback_tokens
        else:
            # Last resort: use original content with minimal cleanup
            optimized_content = specification.content
            optimized_tokens = specification.token_count
            cleaned = re.sub(r"\n\n\n+", "\n\n", optimized_content)
            cleaned = re.sub(r"  +", " ", cleaned)
            cleaned_tokens = count_tokens(cleaned)
            if cleaned_tokens < optimized_tokens:
                optimized_content = cleaned
                optimized_tokens = cleaned_tokens

    # Calculate compression ratio
    if optimized_tokens >= specification.token_count:
        compression_ratio = 0.0
    else:
        compression_ratio = calculate_compression_ratio(specification.token_count, optimized_tokens)

    # Build section lists
    for section_name, metrics in sections_breakdown.items():
        if metrics.action_taken in ("preserved"):
            sections_preserved.append(section_name)
        else:
            sections_compressed.append(section_name)

    # Create metadata with Huffman codebook
    metadata = DigestMetadata(
        source_hash=specification.hash,
        format_version="1.1",
        optimization_profile=profile.name,
        sections_compressed=sections_compressed,
        sections_preserved=sections_preserved,
        generator_version=__version__,
        timestamp=datetime.now(),
        huffman_codebook=huffman_codebook.to_dict() if huffman_codebook.encodings else None,
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
            if optimized_tokens >= original_tokens:
                reduction = 0.0
            else:
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
                if optimized_tokens >= original_tokens:
                    reduction = 0.0
                else:
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


# ============================================================================
# Batch Processing Functions (Feature: 002-directory-digest)
# ============================================================================

# Default file patterns for directory scanning
DEFAULT_FILE_PATTERNS = ["*.md", "*.yaml", "*.yml", "*.json"]


def discover_files(
    directory: Path,
    patterns: list[str] | None = None,
    recursive: bool = True,
) -> DirectoryScanResult:
    """Discover specification files in directory using glob patterns.

    Args:
        directory: Directory to scan
        patterns: File patterns to match (default: DEFAULT_FILE_PATTERNS)
        recursive: Whether to scan subdirectories (default: True)

    Returns:
        DirectoryScanResult with discovered files

    Raises:
        ValueError: If no files found matching patterns
    """
    patterns = patterns or DEFAULT_FILE_PATTERNS.copy()

    files = []
    for pattern in patterns:
        if recursive:
            files.extend(directory.rglob(pattern))
        else:
            files.extend(directory.glob(pattern))

    # Remove duplicates, exclude digest output files, and sort for deterministic ordering
    files = sorted(f for f in set(files) if ".digest." not in f.name)

    result = DirectoryScanResult(
        input_path=directory,
        files_found=files,
        total_count=len(files),
        patterns_used=patterns,
        recursive=recursive,
    )

    # Validate that files were found
    result.validate()

    return result


def process_batch(
    files: list[Path],
    profile: OptimizationProfile,
    format_option: FormatEnum | None = None,
    dry_run: bool = False,
    force: bool = False,
    fail_fast: bool = False,
) -> ProcessingSummary:
    """Process multiple files in batch mode with progress tracking.

    Args:
        files: List of files to process
        profile: Optimization profile to apply
        format_option: Output format override (or None to preserve)
        dry_run: Preview mode - don't write files
        force: Overwrite without prompting
        fail_fast: Stop on first error

    Returns:
        ProcessingSummary with aggregate results
    """
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
    )

    from specnut.cli.styles import console

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing files...", total=len(files))

        for idx, file_path in enumerate(files, 1):
            progress.update(
                task,
                description=f"Processing {idx}/{len(files)}: {file_path.name}",
            )

            try:
                start_time = time.time()

                # Load specification using factory method
                spec = Specification.from_file(file_path)

                # Generate digest
                digest_obj, _ = generate_digest(spec, profile, format_option)

                # Generate output path based on format
                if format_option:
                    ext = f".{format_option.value}"
                else:
                    ext = file_path.suffix

                output_path = file_path.parent / f"{file_path.stem}.digest{ext}"

                # Write digest (unless dry-run)
                if not dry_run:
                    # Check if file exists
                    if output_path.exists() and not force:
                        # Skip if exists and not forcing
                        result = FileProcessingResult(
                            file_path=file_path,
                            status=ProcessingStatus.SKIPPED,
                            original_tokens=spec.token_count,
                            digest_tokens=digest_obj.token_count,
                            processing_time_ms=int((time.time() - start_time) * 1000),
                            output_path=output_path,
                            error_message="File exists (use --force to overwrite)",
                        )
                        results.append(result)
                        progress.advance(task)
                        continue

                    # Write digest file using to_file method
                    digest_obj.to_file(output_path)

                # Record success
                processing_time = int((time.time() - start_time) * 1000)
                result = FileProcessingResult.create_success(
                    file_path=file_path,
                    original_tokens=spec.token_count,
                    digest_tokens=digest_obj.token_count,
                    output_path=output_path,
                    processing_time_ms=processing_time,
                )
                results.append(result)

            except Exception as e:
                # Record failure
                result = FileProcessingResult.create_failure(file_path=file_path, error=e)
                results.append(result)

                # Handle fail-fast mode
                if fail_fast:
                    from specnut.cli.styles import print_error

                    print_error(
                        "Processing Failed", f"{file_path}: {type(e).__name__}: {str(e)}"
                    )
                    # Return partial summary
                    return ProcessingSummary.from_results(results)

            progress.advance(task)

    return ProcessingSummary.from_results(results)
