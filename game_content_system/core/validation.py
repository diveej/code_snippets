"""Validation primitives used by every game-type schema.

The rule from the plan: content cannot move past DRAFT until it passes
`validate()`. Each game type defines its own rules (see Phase 5) but they all
emit `ValidationResult`.
"""

from dataclasses import dataclass, field
from typing import List


class ValidationError(Exception):
    """Raised when attempting to publish invalid content."""


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def merge(self, other: "ValidationResult") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def raise_if_failed(self) -> None:
        if not self.ok:
            raise ValidationError("; ".join(self.errors))
