"""Rubric — manual review criteria; optional per-task or per-content."""

from dataclasses import dataclass, field
from typing import List
from uuid import uuid4


@dataclass
class RubricCriterion:
    name: str
    description: str
    max_points: int = 5


@dataclass
class Rubric:
    name: str
    criteria: List[RubricCriterion] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid4().hex)

    @property
    def total_points(self) -> int:
        return sum(c.max_points for c in self.criteria)
