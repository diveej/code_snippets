"""AI Scenario Conversation — a guided thinking game, not a chatbot.

Key rule from the plan: the AI pushes back, disagrees sometimes, and makes
the student defend their thinking. This schema is the admin-authored data
that feeds the runtime AI scenario engine (Phase 7).
"""

from dataclasses import dataclass, field
from typing import List, Optional

from game_content_system.core.base import ContentBase
from game_content_system.core.enums import AIStrictness, GameType
from game_content_system.core.validation import ValidationResult


@dataclass
class ReasoningTarget:
    """A point the student's reasoning should reach for full credit."""

    label: str
    description: str
    weight: float = 1.0
    keywords: List[str] = field(default_factory=list)


@dataclass
class AnswerPattern:
    """Admin-described shape of a strong, weak, or bad answer."""

    label: str
    description: str
    example: Optional[str] = None


@dataclass
class PushbackLine:
    trigger: str  # admin-described trigger, e.g. "student over-generalizes"
    line: str  # what the AI might say


@dataclass
class HintLine:
    level: int  # 1 = nudge, 3 = near-spoiler
    line: str


@dataclass
class AIScenarioConversation(ContentBase):
    game_type: GameType = GameType.AI_SCENARIO_CONVERSATION

    scenario_title: str = ""
    scenario_setup: str = ""
    background_info: str = ""
    what_to_figure_out: str = ""

    target_reasoning_map: List[ReasoningTarget] = field(default_factory=list)

    strong_answer_patterns: List[AnswerPattern] = field(default_factory=list)
    weak_answer_patterns: List[AnswerPattern] = field(default_factory=list)
    common_bad_answers: List[AnswerPattern] = field(default_factory=list)

    pushback_lines: List[PushbackLine] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    hint_lines: List[HintLine] = field(default_factory=list)

    ai_strictness: AIStrictness = AIStrictness.BALANCED
    minimum_turns: int = 4

    # Completion logic: pass when the student hits `required_targets_hit` of
    # the target reasoning map at the configured strictness, AND reaches the
    # minimum turn count.
    required_targets_hit: int = 3

    def validate(self) -> ValidationResult:
        result = self.validate_base()

        if self.game_type != GameType.AI_SCENARIO_CONVERSATION:
            result.add_error("game_type must be ai_scenario_conversation")

        if not self.scenario_setup.strip():
            result.add_error("scenario_setup is required")
        if not self.what_to_figure_out.strip():
            result.add_error("what_to_figure_out is required")

        if not self.target_reasoning_map:
            result.add_error("target_reasoning_map must have at least 1 target")

        for i, t in enumerate(self.target_reasoning_map):
            if not t.label.strip() or not t.description.strip():
                result.add_error(f"target[{i}]: label and description are required")
            if t.weight <= 0:
                result.add_error(f"target[{i}]: weight must be > 0")

        if not (self.pushback_lines or self.follow_up_questions):
            result.add_error(
                "must have at least 1 pushback_line or follow_up_question — "
                "without these the AI cannot push the student's thinking"
            )

        if self.minimum_turns < 1:
            result.add_error("minimum_turns must be >= 1")

        if self.required_targets_hit < 1:
            result.add_error("required_targets_hit must be >= 1")
        if self.required_targets_hit > len(self.target_reasoning_map):
            result.add_error(
                "required_targets_hit exceeds number of targets in the reasoning map"
            )

        # Plan rule: don't let this degrade into a normal chatbot.
        if not self.common_bad_answers:
            result.add_warning(
                "no common_bad_answers defined — AI cannot recognize weak reasoning "
                "as well without examples"
            )
        if not self.hint_lines:
            result.add_warning(
                "no hint_lines — struggling students get no scaffolding"
            )
        if self.minimum_turns < 3 and self.ai_strictness == AIStrictness.STRICT:
            result.add_warning(
                "strict strictness with minimum_turns<3 — too few turns to verify reasoning"
            )
        return result
