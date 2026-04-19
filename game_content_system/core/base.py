"""Shared `content_base` — fields every game type carries.

All fields have defaults so admins can save partial drafts. `validate()`
(on the subclass) is what gates promotion out of DRAFT.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from game_content_system.core.enums import (
    Difficulty,
    GameType,
    ReviewMode,
    Status,
    SubmissionType,
)
from game_content_system.core.validation import ValidationResult


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid4().hex


@dataclass
class ScoringRules:
    pass_threshold: float = 0.7
    max_score: int = 100
    attempts_allowed: int = 3
    partial_credit: bool = True


@dataclass
class ModerationSettings:
    review_mode: ReviewMode = ReviewMode.AUTO_PASS
    reviewer_group: Optional[str] = None
    require_two_reviewers: bool = False


@dataclass
class ContentBase:
    """Shared fields for every game, regardless of type.

    Subclasses override `game_type` and add mode-specific config fields.
    Every field has a default so partial drafts are valid storage-wise;
    `validate()` enforces required fields before publish.
    """

    title: str = ""
    game_type: GameType = GameType.INSTRUCTIONAL_MISSION
    learning_goal: str = ""
    pass_criteria: str = ""
    short_description: str = ""
    difficulty: Difficulty = Difficulty.BEGINNER
    estimated_time_minutes: int = 10
    submission_type: SubmissionType = SubmissionType.TEXT
    scoring_rules: ScoringRules = field(default_factory=ScoringRules)
    moderation: ModerationSettings = field(default_factory=ModerationSettings)
    tags: List[str] = field(default_factory=list)
    thumbnail_asset_id: Optional[str] = None

    status: Status = Status.DRAFT
    version: int = 1
    id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    published_at: Optional[datetime] = None

    def validate_base(self) -> ValidationResult:
        result = ValidationResult()
        if not self.title.strip():
            result.add_error("title is required")
        if len(self.title) > 120:
            result.add_error("title must be <= 120 chars")
        if not self.learning_goal.strip():
            result.add_error("learning_goal is required")
        if not self.pass_criteria.strip():
            result.add_error("pass_criteria is required")
        if not self.short_description.strip():
            result.add_warning("short_description is empty — students see this in the catalog")
        if self.estimated_time_minutes <= 0:
            result.add_error("estimated_time_minutes must be > 0")
        if not 0 < self.scoring_rules.pass_threshold <= 1:
            result.add_error("pass_threshold must be between 0 and 1")
        if self.scoring_rules.attempts_allowed < 1:
            result.add_error("attempts_allowed must be >= 1")
        return result
