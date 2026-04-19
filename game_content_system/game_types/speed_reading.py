"""Speed Reading Ladder — timed reading + comprehension.

Key rule from the plan: do not let this become speed only. A student passes
only if reading speed AND comprehension both meet their thresholds.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from game_content_system.core.base import ContentBase
from game_content_system.core.enums import GameType, ReadingLevel
from game_content_system.core.validation import ValidationResult


@dataclass
class ComprehensionQuestion:
    prompt: str
    choices: List[str]
    correct_index: int
    explanation: Optional[str] = None


@dataclass
class ReadingPassage:
    text: str
    word_count: int = 0
    source: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.word_count:
            self.word_count = len(self.text.split())


@dataclass
class SpeedReadingLadder(ContentBase):
    game_type: GameType = GameType.SPEED_READING_LADDER

    passages: List[ReadingPassage] = field(default_factory=list)
    reading_level: ReadingLevel = ReadingLevel.ADULT

    timer_seconds: int = 60
    target_wpm: int = 250

    questions: List[ComprehensionQuestion] = field(default_factory=list)
    comprehension_threshold: float = 0.7

    # Ladder / promotion
    level_number: int = 1
    promote_on_pass: bool = True
    next_level_id: Optional[str] = None

    def validate(self) -> ValidationResult:
        result = self.validate_base()

        if self.game_type != GameType.SPEED_READING_LADDER:
            result.add_error("game_type must be speed_reading_ladder")

        if not self.passages:
            result.add_error("must have at least 1 passage")
        for i, p in enumerate(self.passages):
            if not p.text.strip():
                result.add_error(f"passage[{i}]: text is required")
            if p.word_count < 20:
                result.add_warning(f"passage[{i}]: very short ({p.word_count} words)")

        if not self.questions:
            result.add_error("must have comprehension questions")
        for i, q in enumerate(self.questions):
            prefix = f"question[{i}]"
            if not q.prompt.strip():
                result.add_error(f"{prefix}: prompt is required")
            if len(q.choices) < 2:
                result.add_error(f"{prefix}: must have >= 2 choices")
            if not 0 <= q.correct_index < len(q.choices):
                result.add_error(f"{prefix}: correct_index out of range")

        if self.timer_seconds <= 0:
            result.add_error("timer_seconds must be > 0")
        if self.target_wpm <= 0:
            result.add_error("target_wpm must be > 0")
        if not 0 < self.comprehension_threshold <= 1:
            result.add_error("comprehension_threshold must be between 0 and 1")

        # Enforce the plan's core rule: both speed and comprehension required.
        if self.comprehension_threshold < 0.5:
            result.add_warning(
                "comprehension_threshold below 0.5 — students can pass by guessing"
            )
        if self.promote_on_pass and not self.next_level_id and self.level_number > 0:
            result.add_warning(
                "promote_on_pass is true but next_level_id not set — "
                "students pass with no next rung on the ladder"
            )
        return result
