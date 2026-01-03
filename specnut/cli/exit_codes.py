"""POSIX exit codes for SpecNut CLI."""

from enum import IntEnum


class ExitCode(IntEnum):
    """POSIX-compliant exit codes for SpecNut CLI.

    Attributes:
        SUCCESS: Operation completed successfully (0)
        GENERAL_ERROR: General error - invalid arguments, missing files,
            unexpected errors (1)
        VALIDATION_ERROR: Input validation failed - unsupported format,
            invalid content (2)
        COMPRESSION_ERROR: Compression requirements not met - failed to
            achieve minimum 30% reduction (3)
        IO_ERROR: File I/O operation failed - can't read input, can't
            write output (4)
        DEPENDENCY_ERROR: Missing or incompatible dependency (5)
    """

    SUCCESS = 0
    GENERAL_ERROR = 1
    VALIDATION_ERROR = 2
    COMPRESSION_ERROR = 3
    IO_ERROR = 4
    DEPENDENCY_ERROR = 5

    def __str__(self) -> str:
        """Return string representation with code value."""
        return f"{self.name} (code {self.value})"
