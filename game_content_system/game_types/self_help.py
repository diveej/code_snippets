"""Self-Help Framework Builder — read an idea, show you get it.

Key rule from the plan: there should be at least one application step, not
just recall. If they read about e.g. the four laws of leverage, they must
have to explain or apply it.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from game_content_system.core.base import ContentBase
from game_content_system.core.enums import CompletionRule, GameType
from game_content_system.core.validation import ValidationResult


@dataclass
class Concept:
    name: str
    summary: str
    examples: List[str] = field(default_factory=list)


@dataclass
class ReflectionPrompt:
    prompt: str
    min_words: int = 40


@dataclass
class QuizQuestion:
    prompt: str
    choices: List[str]
    correct_index: int
    explanation: Optional[str] = None


@dataclass
class ApplicationTask:
    """Real-world application — student explains or applies the framework."""

    title: str
    instructions: str
    min_words: int = 80
    rubric_id: Optional[str] = None


@dataclass
class SelfHelpFramework(ContentBase):
    game_type: GameType = GameType.SELF_HELP_FRAMEWORK

    framework_name: str = ""
    lesson_content: str = ""
    key_concepts: List[Concept] = field(default_factory=list)

    reflection_prompts: List[ReflectionPrompt] = field(default_factory=list)
    quiz_questions: List[QuizQuestion] = field(default_factory=list)
    application_tasks: List[ApplicationTask] = field(default_factory=list)

    completion_rule: CompletionRule = CompletionRule.MIXED

    def validate(self) -> ValidationResult:
        result = self.validate_base()

        if self.game_type != GameType.SELF_HELP_FRAMEWORK:
            result.add_error("game_type must be self_help_framework")

        if not self.framework_name.strip():
            result.add_error("framework_name is required")
        if not self.lesson_content.strip():
            result.add_error("lesson_content is required")
        if not self.key_concepts:
            result.add_error("must have at least 1 key concept")

        for i, c in enumerate(self.key_concepts):
            if not c.name.strip() or not c.summary.strip():
                result.add_error(f"concept[{i}]: name and summary are required")

        has_reflection = bool(self.reflection_prompts)
        has_quiz = bool(self.quiz_questions)
        has_application = bool(self.application_tasks)

        if not (has_reflection or has_quiz or has_application):
            result.add_error(
                "must have at least 1 reflection, quiz, or application task"
            )

        # Completion rule must match what is actually provided
        rule = self.completion_rule
        if rule == CompletionRule.QUIZ_ONLY and not has_quiz:
            result.add_error("completion_rule=quiz_only but no quiz_questions")
        if rule == CompletionRule.REFLECTION_ONLY and not has_reflection:
            result.add_error("completion_rule=reflection_only but no reflection_prompts")
        if rule == CompletionRule.APPLICATION_ONLY and not has_application:
            result.add_error("completion_rule=application_only but no application_tasks")
        if rule == CompletionRule.MIXED and sum([has_reflection, has_quiz, has_application]) < 2:
            result.add_error("completion_rule=mixed requires at least 2 completion types")

        # Plan rule: prefer application over pure recall.
        if not has_application:
            result.add_warning(
                "no application_tasks — framework risks being pure recall; "
                "add at least one task where the student applies the idea"
            )

        for i, q in enumerate(self.quiz_questions):
            prefix = f"quiz[{i}]"
            if not q.prompt.strip():
                result.add_error(f"{prefix}: prompt is required")
            if len(q.choices) < 2:
                result.add_error(f"{prefix}: must have >= 2 choices")
            if not 0 <= q.correct_index < len(q.choices):
                result.add_error(f"{prefix}: correct_index out of range")

        for i, t in enumerate(self.application_tasks):
            if not t.title.strip() or not t.instructions.strip():
                result.add_error(f"application[{i}]: title and instructions are required")

        return result
