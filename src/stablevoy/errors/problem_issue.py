from dataclasses import dataclass


@dataclass(frozen=True)
class ProblemIssue:
    """A field a validation error names."""

    path: str
    message: str
