"""Submission + Evaluation — what the student turns in, what it scored.

AI scenario mode stores the full transcript on the submission.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from game_content_system.core.enums import GameType, SubmissionType


class EvaluationOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


@dataclass
class ConversationTurn:
    role: str  # "student" | "ai"
    text: str
    targets_hit: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Submission:
    content_id: str
    content_version: int
    student_id: str
    game_type: GameType
    submission_type: SubmissionType

    # One of these is populated based on submission_type:
    text_answer: Optional[str] = None
    asset_ids: List[str] = field(default_factory=list)
    quiz_answers: Dict[str, int] = field(default_factory=dict)  # question_idx -> choice
    reading_duration_seconds: Optional[float] = None
    conversation: List[ConversationTurn] = field(default_factory=list)

    attempt_number: int = 1
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Evaluation:
    submission_id: str
    outcome: EvaluationOutcome
    score: float
    max_score: float
    feedback: str = ""
    reviewer_id: Optional[str] = None  # None => auto-evaluated
    criterion_scores: Dict[str, float] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def passed(self) -> bool:
        return self.outcome == EvaluationOutcome.PASS
