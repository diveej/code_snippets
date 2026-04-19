"""Tests for Phase 5 validation rules — one happy path and the key
failure modes per game type.
"""

import unittest

from game_content_system import (
    GameType,
    Status,
    ValidationError,
    registry,
)
from game_content_system.core.enums import (
    AIStrictness,
    CompletionRule,
    ProofType,
)
from game_content_system.game_types import (
    AIScenarioConversation,
    AnswerPattern,
    ComprehensionQuestion,
    Concept,
    HintLine,
    InstructionalMission,
    InstructionalStep,
    PushbackLine,
    QuizQuestion,
    ReadingPassage,
    ReasoningTarget,
    ReflectionPrompt,
    ApplicationTask,
    SelfHelpFramework,
    SpeedReadingLadder,
)


def _base_kwargs(**overrides):
    defaults = dict(
        title="Sample",
        learning_goal="Learn something concrete",
        pass_criteria="Finish the task",
        short_description="Short blurb",
    )
    defaults.update(overrides)
    return defaults


# ---------- Instructional Mission -----------------------------------------


class TestInstructionalMission(unittest.TestCase):
    def _valid(self) -> InstructionalMission:
        return InstructionalMission(
            **_base_kwargs(),
            goal="Install the thing",
            final_result_image_asset_id="asset_final",
            steps=[
                InstructionalStep(order=1, screenshot_asset_id="a1", instruction="Click X"),
                InstructionalStep(order=2, screenshot_asset_id="a2", instruction="Click Y"),
            ],
            required_proof_type=ProofType.SCREENSHOT,
            submission_instructions="Upload a final screenshot",
            pass_rule="Screenshot matches the final result",
        )

    def test_valid(self):
        self.assertTrue(self._valid().validate().ok)

    def test_requires_final_result_image(self):
        m = self._valid()
        m.final_result_image_asset_id = ""
        r = m.validate()
        self.assertFalse(r.ok)
        self.assertTrue(any("final_result_image" in e for e in r.errors))

    def test_requires_at_least_one_step(self):
        m = self._valid()
        m.steps = []
        self.assertFalse(m.validate().ok)

    def test_duplicate_step_order_fails(self):
        m = self._valid()
        m.steps[1].order = m.steps[0].order
        self.assertFalse(m.validate().ok)

    def test_step_requires_instruction_and_screenshot(self):
        m = self._valid()
        m.steps[0].instruction = ""
        m.steps[0].screenshot_asset_id = ""
        r = m.validate()
        self.assertFalse(r.ok)


# ---------- Speed Reading Ladder ------------------------------------------


class TestSpeedReadingLadder(unittest.TestCase):
    def _valid(self) -> SpeedReadingLadder:
        return SpeedReadingLadder(
            **_base_kwargs(),
            passages=[ReadingPassage(text="The quick brown fox " * 40)],
            questions=[
                ComprehensionQuestion(
                    prompt="What animal?",
                    choices=["fox", "cat", "dog"],
                    correct_index=0,
                ),
            ],
            timer_seconds=60,
            target_wpm=250,
            comprehension_threshold=0.7,
            next_level_id="level_2",
        )

    def test_valid(self):
        self.assertTrue(self._valid().validate().ok)

    def test_requires_passage(self):
        m = self._valid()
        m.passages = []
        self.assertFalse(m.validate().ok)

    def test_requires_questions(self):
        m = self._valid()
        m.questions = []
        self.assertFalse(m.validate().ok)

    def test_bad_correct_index(self):
        m = self._valid()
        m.questions[0].correct_index = 99
        self.assertFalse(m.validate().ok)

    def test_low_comprehension_warns(self):
        m = self._valid()
        m.comprehension_threshold = 0.3
        r = m.validate()
        self.assertTrue(r.ok)
        self.assertTrue(any("guessing" in w for w in r.warnings))


# ---------- Self-Help Framework -------------------------------------------


class TestSelfHelpFramework(unittest.TestCase):
    def _valid(self) -> SelfHelpFramework:
        return SelfHelpFramework(
            **_base_kwargs(),
            framework_name="Four Laws of Leverage",
            lesson_content="The four laws are ...",
            key_concepts=[Concept(name="Capital", summary="Money works for you")],
            reflection_prompts=[ReflectionPrompt(prompt="Where could you apply this?")],
            quiz_questions=[
                QuizQuestion(
                    prompt="Which law uses money?",
                    choices=["Capital", "Code", "Media"],
                    correct_index=0,
                )
            ],
            application_tasks=[
                ApplicationTask(
                    title="Apply capital law",
                    instructions="Describe one way to use capital leverage in your life.",
                )
            ],
            completion_rule=CompletionRule.MIXED,
        )

    def test_valid(self):
        self.assertTrue(self._valid().validate().ok)

    def test_requires_at_least_one_response_type(self):
        m = self._valid()
        m.reflection_prompts = []
        m.quiz_questions = []
        m.application_tasks = []
        m.completion_rule = CompletionRule.REFLECTION_ONLY
        self.assertFalse(m.validate().ok)

    def test_mixed_requires_two_types(self):
        m = self._valid()
        m.reflection_prompts = []
        m.application_tasks = []
        # Only quiz remains -> MIXED is invalid
        self.assertFalse(m.validate().ok)

    def test_application_only_requires_application(self):
        m = self._valid()
        m.completion_rule = CompletionRule.APPLICATION_ONLY
        m.application_tasks = []
        self.assertFalse(m.validate().ok)

    def test_no_application_warns(self):
        m = self._valid()
        m.application_tasks = []
        m.completion_rule = CompletionRule.MIXED  # still valid with reflection+quiz
        r = m.validate()
        self.assertTrue(r.ok)
        self.assertTrue(any("application" in w for w in r.warnings))


# ---------- AI Scenario Conversation --------------------------------------


class TestAIScenarioConversation(unittest.TestCase):
    def _valid(self) -> AIScenarioConversation:
        return AIScenarioConversation(
            **_base_kwargs(),
            scenario_title="Pricing Dilemma",
            scenario_setup="You're launching a SaaS at $29/mo ...",
            what_to_figure_out="Pick a pricing model and defend it.",
            target_reasoning_map=[
                ReasoningTarget(label="segment", description="Identify the buyer segment"),
                ReasoningTarget(label="value", description="Articulate value vs. price"),
                ReasoningTarget(label="tradeoff", description="Surface a tradeoff"),
            ],
            strong_answer_patterns=[
                AnswerPattern(label="strong", description="Names segment + quantifies value"),
            ],
            weak_answer_patterns=[
                AnswerPattern(label="weak", description="Generic 'charge more'"),
            ],
            common_bad_answers=[
                AnswerPattern(label="bad", description="Copies competitor blindly"),
            ],
            pushback_lines=[PushbackLine(trigger="generic answer", line="Why specifically?")],
            follow_up_questions=["What would you do differently for enterprise?"],
            hint_lines=[HintLine(level=1, line="Think about the buyer first.")],
            ai_strictness=AIStrictness.BALANCED,
            minimum_turns=4,
            required_targets_hit=2,
        )

    def test_valid(self):
        r = self._valid().validate()
        self.assertTrue(r.ok, r.errors)

    def test_requires_reasoning_map(self):
        m = self._valid()
        m.target_reasoning_map = []
        self.assertFalse(m.validate().ok)

    def test_requires_pushback_or_followup(self):
        m = self._valid()
        m.pushback_lines = []
        m.follow_up_questions = []
        r = m.validate()
        self.assertFalse(r.ok)
        self.assertTrue(any("pushback" in e or "follow_up" in e for e in r.errors))

    def test_required_targets_hit_exceeds_map(self):
        m = self._valid()
        m.required_targets_hit = 99
        self.assertFalse(m.validate().ok)

    def test_strict_low_turns_warns(self):
        m = self._valid()
        m.minimum_turns = 2
        m.ai_strictness = AIStrictness.STRICT
        r = m.validate()
        self.assertTrue(r.ok)
        self.assertTrue(any("strict" in w.lower() for w in r.warnings))


# ---------- Registry ------------------------------------------------------


class TestRegistry(unittest.TestCase):
    def test_registry_lists_all_four_types(self):
        types = {e.game_type for e in registry.list()}
        self.assertEqual(
            types,
            {
                GameType.INSTRUCTIONAL_MISSION,
                GameType.SPEED_READING_LADDER,
                GameType.SELF_HELP_FRAMEWORK,
                GameType.AI_SCENARIO_CONVERSATION,
            },
        )

    def test_new_draft_returns_right_subclass(self):
        draft = registry.new_draft(GameType.SPEED_READING_LADDER)
        self.assertIsInstance(draft, SpeedReadingLadder)
        self.assertEqual(draft.status, Status.DRAFT)

    def test_publish_blocks_invalid_content(self):
        draft = registry.new_draft(GameType.INSTRUCTIONAL_MISSION)
        with self.assertRaises(ValidationError):
            registry.publish(draft)
        self.assertEqual(draft.status, Status.DRAFT)

    def test_publish_valid_content_flips_status(self):
        m = InstructionalMission(
            **_base_kwargs(),
            goal="Do the thing",
            final_result_image_asset_id="a_final",
            steps=[InstructionalStep(order=1, screenshot_asset_id="a1", instruction="Step 1")],
            submission_instructions="Upload proof",
            pass_rule="Matches result",
        )
        registry.publish(m)
        self.assertEqual(m.status, Status.PUBLISHED)
        self.assertIsNotNone(m.published_at)


if __name__ == "__main__":
    unittest.main()
