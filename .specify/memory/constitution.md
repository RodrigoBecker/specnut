<!--
================================================================================
SYNC IMPACT REPORT
================================================================================
Version Change: Initial → 1.0.0
Modified Principles: N/A (initial constitution)
Added Sections:
  - I. Tool-First Development
  - II. Test-First Discipline (NON-NEGOTIABLE)
  - III. Observability & Debugging
  - IV. Semantic Versioning & Breaking Changes
  - V. Simplicity & YAGNI
  - VI. Documentation Standards
  - VII. Output Format Flexibility
Removed Sections: N/A (initial constitution)
Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md (Constitution Check section aligned)
  ✅ .specify/templates/spec-template.md (requirements section aligned)
  ✅ .specify/templates/tasks-template.md (testing discipline aligned)
Follow-up TODOs: None
================================================================================
-->

# SpecNut Constitution

## Core Principles

### I. Tool-First Development

SpecNut is a CLI tool for generating ultra-compact specification digests. Every
feature MUST be accessible via command-line interface with clear input/output
contracts. Features exist to serve the end user running the tool, not to create
internal abstractions for their own sake.

**Requirements**:

- All functionality MUST be invocable via CLI with explicit arguments or stdin
- Text-based I/O protocol: inputs via stdin/args → outputs to stdout, errors to stderr
- Support multiple output formats (JSON, YAML, Markdown, compact) where applicable
- Each command MUST have clear, documented usage examples
- Exit codes MUST follow POSIX conventions (0=success, non-zero=error)

**Rationale**: SpecNut's value is in the tool itself. A great CLI is the product,
not a wrapper around libraries. Users interact with commands, not code.

### II. Test-First Discipline (NON-NEGOTIABLE)

Test-Driven Development (TDD) is MANDATORY for all feature work. Tests MUST be
written first, reviewed and approved by the user, verified to fail, and only
then can implementation proceed. This is the Red-Green-Refactor cycle strictly
enforced.

**Requirements**:

- Write tests BEFORE implementation (no exceptions)
- Tests MUST fail initially (red phase verified)
- User MUST approve test scenarios before implementation begins
- Implementation makes tests pass (green phase)
- Refactor only after tests pass
- No feature PR can be merged without tests

**Rationale**: TDD ensures we build what's needed, provides living documentation,
enables fearless refactoring, and catches regressions. Skipping tests creates
technical debt that compounds over time.

### III. Observability & Debugging

SpecNut MUST be debuggable in production environments. All operations that
transform, compress, or analyze specifications MUST produce audit trails.
Users should be able to understand what the tool did, why, and trace any
unexpected behavior.

**Requirements**:

- Structured logging for all digest generation operations
- Include metadata in output: source hash, generation timestamp, format version
- Log input validation failures with clear error messages
- Provide verbose/debug mode flag for troubleshooting (`--verbose`, `--debug`)
- Track token counts (original vs. digest) for compression metrics
- Log file paths, format detection, and transformation steps

**Rationale**: Specification processing is a black box without observability.
When digests are wrong or unexpected, users need to diagnose why. Text I/O +
structured logs = debuggability.

### IV. Semantic Versioning & Breaking Changes

SpecNut follows strict semantic versioning (MAJOR.MINOR.PATCH). Breaking changes
require major version bumps, new features require minor bumps, and bug fixes use
patch bumps. The digest format itself has its own version to ensure compatibility.

**Requirements**:

- Version format: MAJOR.MINOR.PATCH (e.g., 2.1.3)
- MAJOR: Breaking CLI changes, digest format incompatibilities, removed options
- MINOR: New commands, new output formats, new optional flags
- PATCH: Bug fixes, performance improvements, documentation updates
- Digest format versioning separate from tool versioning (e.g., `format_version: "1.0"`)
- Breaking changes MUST be documented in CHANGELOG with migration guide
- Deprecated features must warn for at least one minor version before removal

**Rationale**: Users depend on SpecNut's output format and CLI interface.
Unexpected breakage destroys trust. Semver provides a contract.

### V. Simplicity & YAGNI

Start simple. Build only what is explicitly needed now. Resist the temptation
to add abstraction layers, configuration options, or features for hypothetical
future needs. Complexity must be justified against real, current requirements.

**Requirements**:

- No feature flags or configuration for features not explicitly requested
- No abstraction layers until at least 3 concrete use cases demand it
- Prefer straightforward code over clever optimizations unless profiling proves necessity
- If a feature can be implemented in 50 lines or 500 lines, choose 50
- Delete unused code immediately - no "just in case" preservation
- Question every dependency: does it solve a real problem we have today?

**Rationale**: Premature abstraction is the root of maintenance hell. Simple
code is easier to debug, test, and modify. YAGNI keeps the codebase navigable
and the tool focused.

### VI. Documentation Standards

Code alone is insufficient. SpecNut MUST have clear documentation for both users
(how to use the tool) and maintainers (how the code works). Undocumented features
are undiscoverable and unmaintainable.

**Requirements**:

- Every CLI command MUST have help text (accessible via `--help`)
- README MUST include installation, quickstart, and common use cases
- Complex algorithms MUST have explanatory comments (why, not what)
- Public functions MUST have docstrings explaining parameters and return values
- Breaking changes MUST be documented in CHANGELOG before release
- Output format specifications MUST be documented (e.g., what each digest format contains)

**Rationale**: Documentation is a force multiplier. Good docs reduce support
burden, enable contributions, and make the tool self-serve. Comments explain
intent where code cannot.

### VII. Output Format Flexibility

SpecNut processes specifications in multiple input formats (YAML, JSON, Markdown)
and generates digests in multiple output formats (compact, detailed, markdown,
JSON). The tool MUST handle format variations gracefully and provide clear
format selection mechanisms.

**Requirements**:

- Auto-detect input format from file extension (`.yaml`, `.yml`, `.json`, `.md`)
- Support explicit output format selection via CLI flag (`--format json|markdown|compact|detailed`)
- Each output format MUST be deterministic (same input → same output)
- Provide format conversion utilities where useful (e.g., YAML → JSON)
- Validate input format before processing, fail fast with clear error messages
- Document format specifications and trade-offs (compact vs. detailed)

**Rationale**: Different use cases need different formats. API integrations need
JSON, humans need Markdown, token-constrained scenarios need compact. Flexibility
serves diverse user needs.

## Quality Gates

### Pre-Implementation Checklist

Before starting any feature implementation, the following MUST be verified:

- [ ] Feature specification written and approved
- [ ] Tests written in TDD style (test-first)
- [ ] Tests reviewed and approved by user
- [ ] Tests run and verified to FAIL (red phase)
- [ ] Constitution compliance verified (all 7 principles considered)

### Pre-Merge Checklist

Before merging any feature branch, the following MUST be verified:

- [ ] All tests pass (green phase)
- [ ] Code has been refactored for clarity (refactor phase)
- [ ] CLI help text updated if command interface changed
- [ ] CHANGELOG updated if user-visible changes made
- [ ] Version bumped according to semver rules
- [ ] Documentation updated (README, docstrings, comments)
- [ ] Observability verified (logging, error messages, debug mode)

## Governance

### Amendment Process

This constitution is the supreme governing document for SpecNut development.
All pull requests, code reviews, and design decisions MUST comply with these
principles. Violations must be explicitly justified and approved.

**Amendment Requirements**:

- Amendments require documentation of rationale
- Breaking changes to principles require MAJOR version bump
- New principles require MINOR version bump
- Clarifications/wording fixes require PATCH version bump
- All amendments MUST include migration plan if principles change behavior
- Templates (plan, spec, tasks) MUST be updated to reflect amended principles

### Complexity Justification

When a feature violates the Simplicity principle (Principle V) or introduces
significant complexity, it MUST be justified in the implementation plan:

| Violation                | Why Needed          | Simpler Alternative Rejected Because  |
|--------------------------|---------------------|---------------------------------------|
| [Specific complexity]    | [Real current need] | [Why simple approach insufficient]    |

### Compliance Review

- All feature PRs MUST include constitution compliance verification
- Code reviews MUST check adherence to Test-First discipline
- Breaking changes MUST follow semantic versioning rules
- Complexity additions MUST be justified in implementation plan

**Version**: 1.0.0 | **Ratified**: 2026-01-02 | **Last Amended**: 2026-01-02
