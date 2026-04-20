"""End-to-end demo of the game content system.

Run:  python -m game_content_system.demo

Creates one draft for each of the 4 game types, prints validation output,
then publishes the valid ones through the registry.
"""

from game_content_system import GameType, Status, registry
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


def _section(title: str) -> None:
    bar = "=" * 60
    print(f"\n{bar}\n {title}\n{bar}")


def _report(content) -> None:
    result = registry.validate(content)
    print(f"  title: {content.title}")
    print(f"  game_type: {content.game_type.value}")
    print(f"  status: {content.status.value}")
    print(f"  valid: {result.ok}")
    for e in result.errors:
        print(f"    ERROR: {e}")
    for w in result.warnings:
        print(f"    warn:  {w}")


def _instructional() -> InstructionalMission:
    return InstructionalMission(
        title="Install and configure the CLI",
        learning_goal="Install the CLI and run the first command",
        pass_criteria="A screenshot of the CLI version output",
        short_description="Your first hands-on mission",
        goal="Get the CLI installed and verify it works",
        final_result_image_asset_id="asset_final_result",
        steps=[
            InstructionalStep(
                order=1,
                screenshot_asset_id="asset_step_1",
                instruction="Open the terminal and run the install command",
                tip="On macOS the terminal lives in Applications/Utilities",
            ),
            InstructionalStep(
                order=2,
                screenshot_asset_id="asset_step_2",
                instruction="Run `cli --version` to confirm the install",
                warning="If you see 'command not found', restart the terminal",
            ),
        ],
        required_proof_type=ProofType.SCREENSHOT,
        submission_instructions="Upload a screenshot of the version output.",
        pass_rule="The screenshot clearly shows a version number.",
    )


def _speed_reading() -> SpeedReadingLadder:
    passage_text = ("Reading quickly without comprehension is useless. "
                    "The goal of the ladder is to push both speed and understanding together. "
                    "Every rung raises the bar on both.") * 6
    return SpeedReadingLadder(
        title="Speed Reading Level 1",
        learning_goal="Read 250 WPM with 70% comprehension",
        pass_criteria="Meet both the speed and comprehension thresholds",
        short_description="First rung of the ladder",
        passages=[ReadingPassage(text=passage_text)],
        questions=[
            ComprehensionQuestion(
                prompt="What is the goal of the ladder?",
                choices=[
                    "Speed only",
                    "Comprehension only",
                    "Both speed and comprehension",
                ],
                correct_index=2,
            ),
            ComprehensionQuestion(
                prompt="What happens each rung?",
                choices=[
                    "Nothing changes",
                    "The bar goes up on both",
                    "Only speed goes up",
                ],
                correct_index=1,
            ),
        ],
        timer_seconds=45,
        target_wpm=250,
        comprehension_threshold=0.7,
        level_number=1,
        next_level_id="level_2",
    )


def _self_help() -> SelfHelpFramework:
    return SelfHelpFramework(
        title="Four Laws of Leverage",
        learning_goal="Understand and apply the four laws of leverage",
        pass_criteria="Correctly explain and apply each law",
        short_description="Labor, capital, code, media",
        framework_name="Four Laws of Leverage",
        lesson_content=(
            "There are four kinds of leverage: labor, capital, code, and media. "
            "The older two require permission. The newer two do not."
        ),
        key_concepts=[
            Concept(name="Labor", summary="Other people working for you"),
            Concept(name="Capital", summary="Money working for you"),
            Concept(name="Code", summary="Software working for you"),
            Concept(name="Media", summary="Content working for you"),
        ],
        reflection_prompts=[
            ReflectionPrompt(
                prompt="Which law do you use today, and which one is under-used?",
                min_words=60,
            ),
        ],
        quiz_questions=[
            QuizQuestion(
                prompt="Which two forms of leverage are permissionless?",
                choices=["Labor + Capital", "Code + Media", "Labor + Media"],
                correct_index=1,
            ),
        ],
        application_tasks=[
            ApplicationTask(
                title="Design a week of code leverage",
                instructions=(
                    "Describe one concrete thing you would build this week to "
                    "create code leverage, including what it automates and who benefits."
                ),
                min_words=120,
            ),
        ],
        completion_rule=CompletionRule.MIXED,
    )


def _ai_scenario() -> AIScenarioConversation:
    return AIScenarioConversation(
        title="Pricing Your First SaaS",
        learning_goal="Defend a pricing choice with real reasoning",
        pass_criteria="Hit 2 of 3 reasoning targets over at least 4 turns",
        short_description="The AI will push back until your logic holds up",
        scenario_title="Pricing dilemma",
        scenario_setup=(
            "You're launching a productivity SaaS. A competitor charges $29/mo. "
            "Your cost to serve a user is about $3/mo. What do you charge, and why?"
        ),
        background_info="Target market: solo founders and freelancers.",
        what_to_figure_out="Pick a price and pricing model, and defend it.",
        target_reasoning_map=[
            ReasoningTarget(
                label="segment",
                description="Identify the buyer segment clearly",
                keywords=["founder", "freelancer", "solo"],
            ),
            ReasoningTarget(
                label="value",
                description="Quantify value delivered vs. price",
                keywords=["time saved", "revenue", "ROI"],
            ),
            ReasoningTarget(
                label="tradeoff",
                description="Surface a real tradeoff in the choice",
                keywords=["tradeoff", "risk", "churn"],
            ),
        ],
        strong_answer_patterns=[
            AnswerPattern(
                label="strong",
                description="Names segment, quantifies value, acknowledges tradeoff",
            ),
        ],
        weak_answer_patterns=[
            AnswerPattern(
                label="weak",
                description="Generic 'charge what feels right' with no reasoning",
            ),
        ],
        common_bad_answers=[
            AnswerPattern(
                label="bad",
                description="Blindly copies competitor price without justification",
            ),
        ],
        pushback_lines=[
            PushbackLine(
                trigger="student copies competitor price with no reasoning",
                line="Why that price specifically? What tells you it's right for YOUR user?",
            ),
            PushbackLine(
                trigger="student ignores the buyer segment",
                line="Who is actually buying this? Be specific.",
            ),
        ],
        follow_up_questions=[
            "What would change your price if churn doubled?",
            "How would you price differently for an enterprise buyer?",
        ],
        hint_lines=[
            HintLine(level=1, line="Start with the buyer, not the competitor."),
            HintLine(level=2, line="What does your user save in time or money each month?"),
        ],
        ai_strictness=AIStrictness.BALANCED,
        minimum_turns=4,
        required_targets_hit=2,
    )


def main() -> None:
    _section("Registered game types")
    for entry in registry.list():
        print(f"  - {entry.label:32s} ({entry.game_type.value})")
        print(f"      {entry.description}")

    samples = [
        ("Instructional Mission", _instructional()),
        ("Speed Reading Ladder", _speed_reading()),
        ("Self-Help Framework", _self_help()),
        ("AI Scenario Conversation", _ai_scenario()),
    ]

    _section("Validating drafts")
    for label, content in samples:
        print(f"\n[{label}]")
        _report(content)

    _section("Publishing valid drafts")
    for label, content in samples:
        print(f"\n[{label}]")
        try:
            registry.publish(content)
            print(f"  published at: {content.published_at}")
            print(f"  new status: {content.status.value}")
        except Exception as e:
            print(f"  publish failed: {e}")

    _section("Demonstrating validation blocks")
    bad = _instructional()
    bad.final_result_image_asset_id = ""  # break the "must see target" rule
    print("\n[Instructional without final_result_image]")
    _report(bad)
    try:
        registry.publish(bad)
    except Exception as e:
        print(f"  publish blocked (good): {e}")
        print(f"  status stayed: {bad.status.value}")


if __name__ == "__main__":
    main()
