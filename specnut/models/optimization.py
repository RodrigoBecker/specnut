"""OptimizationProfile model for compression configuration."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from specnut.models import CompressionLevel, Priority

if TYPE_CHECKING:
    from specnut.models.digest import Digest
    from specnut.models.specification import Specification


@dataclass
class PreserveRule:
    """Rule for what content must be preserved during compression.

    Attributes:
        pattern: Regex pattern to match
        action: Action to take ("preserve" / "compress" / "omit")
        reason: Why this rule exists (for documentation)
    """

    pattern: str
    action: str
    reason: str

    def __post_init__(self):
        """Validate rule after initialization."""
        valid_actions = {"preserve", "compress", "omit"}
        if self.action not in valid_actions:
            raise ValueError(f"Action must be one of {valid_actions}, got '{self.action}'")


@dataclass
class OptimizationProfile:
    """Configuration that defines how specifications are compressed.

    Attributes:
        name: Profile name (default/low/medium/high)
        compression_level: Enum: LOW/MEDIUM/HIGH
        target_reduction: Target compression ratio (0.0 to 1.0)
        section_priorities: Priority map for section types
        preserve_rules: Rules for what must be preserved
        abbreviation_map: Custom abbreviations (e.g., FR → Functional Requirement)
    """

    name: str
    compression_level: CompressionLevel
    target_reduction: float
    section_priorities: dict[str, Priority]
    preserve_rules: list[PreserveRule]
    abbreviation_map: dict[str, str] | None = None

    def __post_init__(self):
        """Validate profile after initialization."""
        if self.target_reduction < 0.0 or self.target_reduction > 0.9:
            raise ValueError(
                f"Target reduction must be between 0.0 and 0.9, got {self.target_reduction}"
            )

        if not self.section_priorities:
            raise ValueError("Section priorities cannot be empty")

    def validate(self) -> None:
        """Ensure profile is internally consistent.

        Raises:
            ValueError: If profile configuration is invalid
        """
        # Validate target reduction matches compression level expectations
        expected_ranges = {
            CompressionLevel.LOW: (0.30, 0.35),
            CompressionLevel.MEDIUM: (0.40, 0.50),
            CompressionLevel.HIGH: (0.55, 0.65),
        }

        min_reduction, max_reduction = expected_ranges[self.compression_level]
        if not (min_reduction <= self.target_reduction <= max_reduction):
            level = self.compression_level.value
            raise ValueError(
                f"Target reduction {self.target_reduction:.2f} is outside expected "
                f"range [{min_reduction:.2f}, {max_reduction:.2f}] for {level} compression"
            )

        # Validate preserve rules
        for rule in self.preserve_rules:
            if not rule.pattern:
                raise ValueError("Preserve rule pattern cannot be empty")

    def apply(self, specification: "Specification") -> "Digest":
        """Execute optimization on a specification.

        This is a placeholder - actual implementation will be in the optimizer module.

        Args:
            specification: Specification to optimize

        Returns:
            Optimized digest

        Raises:
            NotImplementedError: This method will be implemented in the optimizer module
        """
        raise NotImplementedError(
            "Optimization logic will be implemented in specnut.core.optimizer"
        )


# Default optimization profile per data-model.md
DEFAULT_PROFILE = OptimizationProfile(
    name="default",
    compression_level=CompressionLevel.MEDIUM,
    target_reduction=0.40,
    section_priorities={
        # Core sections - preserve requirement IDs but compress descriptions
        "Functional Requirements": Priority.HIGH,
        "Requirements": Priority.HIGH,
        "User Stories": Priority.HIGH,
        "User Scenarios & Testing": Priority.HIGH,
        "Acceptance Criteria": Priority.HIGH,
        "Acceptance Scenarios": Priority.HIGH,
        "Success Criteria": Priority.HIGH,
        # Compressible sections
        "Measurable Outcomes": Priority.MEDIUM,
        "Edge Cases": Priority.MEDIUM,
        "Key Entities": Priority.MEDIUM,
        # Omit or heavily compress these sections
        "Assumptions": Priority.LOW,
        "Implementation Details": Priority.LOW,
        "Examples": Priority.LOW,
        "Technical Context": Priority.LOW,
        "Rationale": Priority.LOW,
        "Background": Priority.LOW,
        "Overview": Priority.LOW,
        "Notes": Priority.LOW,
        "References": Priority.LOW,
    },
    preserve_rules=[
        PreserveRule(
            pattern=r"^\s*-\s+\*\*FR-\d+\*\*:",
            action="preserve",
            reason="Functional requirements must be intact",
        ),
        PreserveRule(
            pattern=r"^\s*-\s+\*\*SC-\d+\*\*:",
            action="preserve",
            reason="Success criteria must be intact",
        ),
        PreserveRule(
            pattern=r"\*\*Given\*\*.*\*\*When\*\*.*\*\*Then\*\*",
            action="preserve",
            reason="Acceptance criteria (BDD format)",
        ),
    ],
    abbreviation_map={
        "Functional Requirement": "FR",
        "User Story": "US",
        "Acceptance Criteria": "AC",
        "Success Criteria": "SC",
        "specification": "spec",
        "implementation": "impl",
        "configuration": "config",
        "application": "app",
    },
)
