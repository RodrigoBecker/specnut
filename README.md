# SpecNut

**CLI tool for optimizing specification digests to reduce token consumption by 30%+**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

SpecNut generates optimized digests from large specification files (YAML, JSON, Markdown), preserving critical information while significantly reducing token count for AI processing.

## Features

- ✅ **30-50% token reduction** on typical specification files
- ✅ **Auto-detect formats** (YAML, JSON, Markdown)
- ✅ **Preserve critical content** (requirements, user stories, acceptance criteria)
- ✅ **Detailed metrics** with section-by-section breakdown
- ✅ **Fast processing** (<10s for 50,000 tokens)
- ✅ **Rich CLI** with styled output
- ✅ **Speckit integration** (optional)

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/specnut/specnut
cd specnut

# Install with Poetry
poetry install

# Or install with pip
pip install -e .
```

### Verify Installation

```bash
specnut --version
# Output: SpecNut v0.1.0
```

## Quick Start

### 1. Basic Usage

Generate a digest from any specification file:

```bash
# Auto-detect format and create digest
specnut digest myspec.md

# Output:
# ✓ Digest generated successfully
#
# Input:  myspec.md (45,234 tokens)
# Output: myspec.digest.md (27,140 tokens)
# Saved:  18,094 tokens (40.0%)
#
# Time:   0.85s
```

### 2. Specify Output Format

```bash
# YAML → JSON
specnut digest spec.yaml -f json -o spec.digest.json

# Markdown → Compact format
specnut digest spec.md -f compact -o spec.compact.txt
```

### 3. Adjust Compression Level

```bash
# Conservative (30-35% reduction)
specnut digest spec.md -c low

# Balanced (40-50% reduction) - DEFAULT
specnut digest spec.md -c medium

# Aggressive (55-65% reduction)
specnut digest spec.md -c high
```

### 4. View Detailed Metrics

```bash
# Show metrics inline
specnut digest spec.md --show-metrics

# Or view metrics later
specnut metrics spec.digest.md

# Detailed breakdown by section
specnut metrics spec.digest.md --breakdown
```

## Commands

### `specnut digest`

Generate optimized specification digest.

**Usage:**
```bash
specnut digest [OPTIONS] INPUT_FILE [OUTPUT_FILE]
```

**Options:**
- `-f, --format`: Output format (auto/yaml/json/markdown/compact)
- `-c, --compression`: Compression level (low/medium/high)
- `-m, --show-metrics`: Display metrics after generation
- `-d, --dry-run`: Preview without writing output
- `--force`: Overwrite existing digest without prompting

### `specnut metrics`

Display token savings metrics.

**Usage:**
```bash
specnut metrics [OPTIONS] DIGEST_FILE
```

**Options:**
- `-f, --format`: Output format (table/json/yaml)
- `-b, --breakdown`: Show per-section breakdown

### `specnut version`

Show version information.

**Usage:**
```bash
specnut version [-f FORMAT]
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/specnut/specnut
cd specnut

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run ruff check .
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=specnut --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_models.py
```

## Project Structure

```
specnut/
├── specnut/              # Main package
│   ├── cli/              # CLI commands
│   ├── core/             # Core logic (parser, optimizer, tokenizer)
│   ├── models/           # Data models
│   └── integrations/     # External integrations
├── tests/                # Test suite
│   ├── contract/         # Contract tests
│   ├── integration/      # Integration tests
│   └── unit/             # Unit tests
└── specs/                # Feature specifications
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/specnut/specnut/issues)
- **Discussions**: [GitHub Discussions](https://github.com/specnut/specnut/discussions)
- **Documentation**: [Full Documentation](https://specnut.dev/docs)

## Acknowledgments

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal styling
- [tiktoken](https://github.com/openai/tiktoken) - Token counting
- [PyYAML](https://pyyaml.org/) - YAML parsing
