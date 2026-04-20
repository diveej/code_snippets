"""Form <-> schema adapters.

For each game type we expose:
    - a list of simple fields (rendered as inputs)
    - a list of JSON fields (rendered as textareas with example JSON)
    - an `apply_form` function that mutates a draft from a form dict

This is deliberately data-driven so templates stay generic.
"""

import json
from dataclasses import asdict, fields, is_dataclass
from typing import Any, Callable, Dict, List, Optional

from game_content_system.core.enums import (
    AIStrictness,
    CompletionRule,
    Difficulty,
    GameType,
    ProofType,
    ReadingLevel,
    ReviewMode,
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


# ---- field descriptors ---------------------------------------------------


class SimpleField:
    def __init__(
        self,
        name: str,
        label: str,
        kind: str = "text",  # text | textarea | int | float | select
        options: Optional[List[str]] = None,
        help: str = "",
    ) -> None:
        self.name = name
        self.label = label
        self.kind = kind
        self.options = options or []
        self.help = help


class JsonField:
    def __init__(
        self,
        name: str,
        label: str,
        help: str,
        example: Any,
        item_cls: Optional[type] = None,
    ) -> None:
        self.name = name
        self.label = label
        self.help = help
        self.example = example
        self.item_cls = item_cls  # dataclass used to rebuild list entries


# ---- shared base fields --------------------------------------------------

BASE_SIMPLE_FIELDS: List[SimpleField] = [
    SimpleField("title", "Title"),
    SimpleField("learning_goal", "Learning goal", kind="textarea"),
    SimpleField("pass_criteria", "Pass criteria", kind="textarea"),
    SimpleField("short_description", "Short description", kind="textarea"),
    SimpleField(
        "difficulty",
        "Difficulty",
        kind="select",
        options=[d.value for d in Difficulty],
    ),
    SimpleField("estimated_time_minutes", "Estimated time (minutes)", kind="int"),
    SimpleField("tags_csv", "Tags (comma separated)"),
    SimpleField("thumbnail_asset_id", "Thumbnail asset id"),
    SimpleField(
        "review_mode",
        "Moderation",
        kind="select",
        options=[r.value for r in ReviewMode],
    ),
    SimpleField("pass_threshold", "Pass threshold (0-1)", kind="float"),
    SimpleField("attempts_allowed", "Attempts allowed", kind="int"),
]


def _apply_base(draft, form: Dict[str, str]) -> None:
    draft.title = form.get("title", "").strip()
    draft.learning_goal = form.get("learning_goal", "").strip()
    draft.pass_criteria = form.get("pass_criteria", "").strip()
    draft.short_description = form.get("short_description", "").strip()

    if form.get("difficulty"):
        draft.difficulty = Difficulty(form["difficulty"])
    if form.get("estimated_time_minutes"):
        draft.estimated_time_minutes = int(form["estimated_time_minutes"])
    if form.get("tags_csv", "").strip():
        draft.tags = [t.strip() for t in form["tags_csv"].split(",") if t.strip()]
    else:
        draft.tags = []
    draft.thumbnail_asset_id = form.get("thumbnail_asset_id", "").strip() or None

    if form.get("review_mode"):
        draft.moderation.review_mode = ReviewMode(form["review_mode"])
    if form.get("pass_threshold"):
        draft.scoring_rules.pass_threshold = float(form["pass_threshold"])
    if form.get("attempts_allowed"):
        draft.scoring_rules.attempts_allowed = int(form["attempts_allowed"])


# ---- JSON helpers --------------------------------------------------------


def _parse_json_list(raw: str, item_cls: type) -> list:
    if not raw.strip():
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError(f"{item_cls.__name__} field must be a JSON list")
    return [_build_dataclass(item_cls, d) for d in data]


def _build_dataclass(cls: type, data: dict):
    if not isinstance(data, dict):
        raise ValueError(f"expected object for {cls.__name__}, got {type(data).__name__}")
    field_names = {f.name for f in fields(cls)}
    clean = {k: v for k, v in data.items() if k in field_names}
    return cls(**clean)


def _dump_example(obj: Any) -> str:
    def default(v):
        if hasattr(v, "value"):
            return v.value
        if is_dataclass(v):
            return asdict(v)
        return str(v)

    return json.dumps(obj, indent=2, default=default)


# ---- per-type specs ------------------------------------------------------


class GameTypeFormSpec:
    def __init__(
        self,
        game_type: GameType,
        extra_simple: List[SimpleField],
        json_fields: List[JsonField],
        apply: Callable[[Any, Dict[str, str]], None],
        defaults: Callable[[], Any],
    ) -> None:
        self.game_type = game_type
        self.extra_simple = extra_simple
        self.json_fields = json_fields
        self.apply = apply
        self.defaults = defaults

    @property
    def simple_fields(self) -> List[SimpleField]:
        return BASE_SIMPLE_FIELDS + self.extra_simple


# ---- Instructional Mission ----------------------------------------------

_INSTRUCTIONAL_STEP_EXAMPLE = [
    {
        "order": 1,
        "screenshot_asset_id": "asset_step_1",
        "instruction": "Open the terminal",
        "tip": "optional",
        "warning": None,
    },
    {
        "order": 2,
        "screenshot_asset_id": "asset_step_2",
        "instruction": "Run the install command",
    },
]


def _apply_instructional(draft: InstructionalMission, form: Dict[str, str]) -> None:
    _apply_base(draft, form)
    draft.goal = form.get("goal", "").strip()
    draft.final_result_image_asset_id = form.get("final_result_image_asset_id", "").strip()
    draft.submission_instructions = form.get("submission_instructions", "").strip()
    draft.pass_rule = form.get("pass_rule", "").strip()
    if form.get("required_proof_type"):
        draft.required_proof_type = ProofType(form["required_proof_type"])
    draft.steps = _parse_json_list(form.get("steps_json", ""), InstructionalStep)


INSTRUCTIONAL_SPEC = GameTypeFormSpec(
    game_type=GameType.INSTRUCTIONAL_MISSION,
    extra_simple=[
        SimpleField("goal", "Goal", kind="textarea"),
        SimpleField("final_result_image_asset_id", "Final result image asset id",
                    help="REQUIRED — students must see the target while doing the steps."),
        SimpleField("submission_instructions", "Submission instructions", kind="textarea"),
        SimpleField("pass_rule", "Pass rule", kind="textarea"),
        SimpleField(
            "required_proof_type",
            "Required proof",
            kind="select",
            options=[p.value for p in ProofType],
        ),
    ],
    json_fields=[
        JsonField(
            "steps_json",
            "Steps (JSON list)",
            help="Each step: order, screenshot_asset_id, instruction, tip?, warning?",
            example=_INSTRUCTIONAL_STEP_EXAMPLE,
            item_cls=InstructionalStep,
        ),
    ],
    apply=_apply_instructional,
    defaults=lambda: InstructionalMission(),
)


# ---- Speed Reading Ladder ------------------------------------------------

_PASSAGES_EXAMPLE = [
    {
        "text": "Your passage text here...",
        "source": "optional",
    },
]
_QUESTIONS_EXAMPLE = [
    {
        "prompt": "What was the main idea?",
        "choices": ["A", "B", "C"],
        "correct_index": 0,
        "explanation": "optional",
    },
]


def _apply_speed_reading(draft: SpeedReadingLadder, form: Dict[str, str]) -> None:
    _apply_base(draft, form)
    if form.get("reading_level"):
        draft.reading_level = ReadingLevel(form["reading_level"])
    if form.get("timer_seconds"):
        draft.timer_seconds = int(form["timer_seconds"])
    if form.get("target_wpm"):
        draft.target_wpm = int(form["target_wpm"])
    if form.get("comprehension_threshold"):
        draft.comprehension_threshold = float(form["comprehension_threshold"])
    if form.get("level_number"):
        draft.level_number = int(form["level_number"])
    draft.next_level_id = form.get("next_level_id", "").strip() or None
    draft.promote_on_pass = form.get("promote_on_pass") == "on"
    draft.passages = _parse_json_list(form.get("passages_json", ""), ReadingPassage)
    draft.questions = _parse_json_list(form.get("questions_json", ""), ComprehensionQuestion)


SPEED_READING_SPEC = GameTypeFormSpec(
    game_type=GameType.SPEED_READING_LADDER,
    extra_simple=[
        SimpleField(
            "reading_level",
            "Reading level",
            kind="select",
            options=[r.value for r in ReadingLevel],
        ),
        SimpleField("timer_seconds", "Timer (seconds)", kind="int"),
        SimpleField("target_wpm", "Target WPM", kind="int"),
        SimpleField("comprehension_threshold", "Comprehension threshold (0-1)", kind="float"),
        SimpleField("level_number", "Level number", kind="int"),
        SimpleField("next_level_id", "Next level id"),
        SimpleField("promote_on_pass", "Promote on pass", kind="checkbox"),
    ],
    json_fields=[
        JsonField("passages_json", "Passages (JSON list)",
                  help="Each: text, source?", example=_PASSAGES_EXAMPLE, item_cls=ReadingPassage),
        JsonField("questions_json", "Comprehension questions (JSON list)",
                  help="Each: prompt, choices[], correct_index, explanation?",
                  example=_QUESTIONS_EXAMPLE, item_cls=ComprehensionQuestion),
    ],
    apply=_apply_speed_reading,
    defaults=lambda: SpeedReadingLadder(),
)


# ---- Self-Help Framework -------------------------------------------------

_CONCEPTS_EXAMPLE = [{"name": "Concept", "summary": "One sentence", "examples": []}]
_REFLECTIONS_EXAMPLE = [{"prompt": "Reflect on X", "min_words": 40}]
_QUIZ_EXAMPLE = [{
    "prompt": "Which law uses money?",
    "choices": ["Capital", "Code"],
    "correct_index": 0,
}]
_APPLICATION_EXAMPLE = [{
    "title": "Apply it",
    "instructions": "Describe how you'd use this in your life.",
    "min_words": 80,
}]


def _apply_self_help(draft: SelfHelpFramework, form: Dict[str, str]) -> None:
    _apply_base(draft, form)
    draft.framework_name = form.get("framework_name", "").strip()
    draft.lesson_content = form.get("lesson_content", "").strip()
    if form.get("completion_rule"):
        draft.completion_rule = CompletionRule(form["completion_rule"])
    draft.key_concepts = _parse_json_list(form.get("concepts_json", ""), Concept)
    draft.reflection_prompts = _parse_json_list(
        form.get("reflections_json", ""), ReflectionPrompt
    )
    draft.quiz_questions = _parse_json_list(form.get("quiz_json", ""), QuizQuestion)
    draft.application_tasks = _parse_json_list(
        form.get("applications_json", ""), ApplicationTask
    )


SELF_HELP_SPEC = GameTypeFormSpec(
    game_type=GameType.SELF_HELP_FRAMEWORK,
    extra_simple=[
        SimpleField("framework_name", "Framework name"),
        SimpleField("lesson_content", "Lesson content", kind="textarea"),
        SimpleField(
            "completion_rule",
            "Completion rule",
            kind="select",
            options=[c.value for c in CompletionRule],
        ),
    ],
    json_fields=[
        JsonField("concepts_json", "Key concepts (JSON list)",
                  help="Each: name, summary, examples[]",
                  example=_CONCEPTS_EXAMPLE, item_cls=Concept),
        JsonField("reflections_json", "Reflection prompts (JSON list)",
                  help="Each: prompt, min_words",
                  example=_REFLECTIONS_EXAMPLE, item_cls=ReflectionPrompt),
        JsonField("quiz_json", "Quiz questions (JSON list)",
                  help="Each: prompt, choices[], correct_index, explanation?",
                  example=_QUIZ_EXAMPLE, item_cls=QuizQuestion),
        JsonField("applications_json", "Application tasks (JSON list)",
                  help="Each: title, instructions, min_words, rubric_id?",
                  example=_APPLICATION_EXAMPLE, item_cls=ApplicationTask),
    ],
    apply=_apply_self_help,
    defaults=lambda: SelfHelpFramework(),
)


# ---- AI Scenario Conversation -------------------------------------------

_TARGETS_EXAMPLE = [
    {"label": "segment", "description": "Identify the buyer segment", "weight": 1.0, "keywords": ["founder"]},
    {"label": "value", "description": "Quantify value vs. price", "weight": 1.0, "keywords": []},
]
_PATTERNS_EXAMPLE = [{"label": "pattern", "description": "describe the pattern", "example": "optional"}]
_PUSHBACK_EXAMPLE = [{"trigger": "generic answer", "line": "Why specifically?"}]
_HINTS_EXAMPLE = [{"level": 1, "line": "Start with the buyer, not the competitor."}]


def _apply_ai_scenario(draft: AIScenarioConversation, form: Dict[str, str]) -> None:
    _apply_base(draft, form)
    draft.scenario_title = form.get("scenario_title", "").strip()
    draft.scenario_setup = form.get("scenario_setup", "").strip()
    draft.background_info = form.get("background_info", "").strip()
    draft.what_to_figure_out = form.get("what_to_figure_out", "").strip()
    if form.get("ai_strictness"):
        draft.ai_strictness = AIStrictness(form["ai_strictness"])
    if form.get("minimum_turns"):
        draft.minimum_turns = int(form["minimum_turns"])
    if form.get("required_targets_hit"):
        draft.required_targets_hit = int(form["required_targets_hit"])
    draft.target_reasoning_map = _parse_json_list(
        form.get("targets_json", ""), ReasoningTarget
    )
    draft.strong_answer_patterns = _parse_json_list(
        form.get("strong_patterns_json", ""), AnswerPattern
    )
    draft.weak_answer_patterns = _parse_json_list(
        form.get("weak_patterns_json", ""), AnswerPattern
    )
    draft.common_bad_answers = _parse_json_list(
        form.get("bad_patterns_json", ""), AnswerPattern
    )
    draft.pushback_lines = _parse_json_list(
        form.get("pushback_json", ""), PushbackLine
    )
    draft.hint_lines = _parse_json_list(form.get("hints_json", ""), HintLine)
    raw_followups = form.get("follow_up_questions_nl", "").strip()
    draft.follow_up_questions = [
        line.strip() for line in raw_followups.splitlines() if line.strip()
    ]


AI_SCENARIO_SPEC = GameTypeFormSpec(
    game_type=GameType.AI_SCENARIO_CONVERSATION,
    extra_simple=[
        SimpleField("scenario_title", "Scenario title"),
        SimpleField("scenario_setup", "Scenario setup", kind="textarea"),
        SimpleField("background_info", "Background info", kind="textarea"),
        SimpleField("what_to_figure_out", "What the student must figure out", kind="textarea"),
        SimpleField(
            "ai_strictness",
            "AI strictness",
            kind="select",
            options=[s.value for s in AIStrictness],
        ),
        SimpleField("minimum_turns", "Minimum turns", kind="int"),
        SimpleField("required_targets_hit", "Required targets hit", kind="int"),
        SimpleField(
            "follow_up_questions_nl",
            "Follow-up questions (one per line)",
            kind="textarea",
        ),
    ],
    json_fields=[
        JsonField("targets_json", "Target reasoning map (JSON list)",
                  help="Each: label, description, weight, keywords[]",
                  example=_TARGETS_EXAMPLE, item_cls=ReasoningTarget),
        JsonField("strong_patterns_json", "Strong answer patterns (JSON list)",
                  help="Each: label, description, example?",
                  example=_PATTERNS_EXAMPLE, item_cls=AnswerPattern),
        JsonField("weak_patterns_json", "Weak answer patterns (JSON list)",
                  help="Each: label, description, example?",
                  example=_PATTERNS_EXAMPLE, item_cls=AnswerPattern),
        JsonField("bad_patterns_json", "Common bad answers (JSON list)",
                  help="Each: label, description, example?",
                  example=_PATTERNS_EXAMPLE, item_cls=AnswerPattern),
        JsonField("pushback_json", "Pushback lines (JSON list)",
                  help="Each: trigger, line",
                  example=_PUSHBACK_EXAMPLE, item_cls=PushbackLine),
        JsonField("hints_json", "Hint lines (JSON list)",
                  help="Each: level (1-3), line",
                  example=_HINTS_EXAMPLE, item_cls=HintLine),
    ],
    apply=_apply_ai_scenario,
    defaults=lambda: AIScenarioConversation(),
)


SPECS: Dict[GameType, GameTypeFormSpec] = {
    GameType.INSTRUCTIONAL_MISSION: INSTRUCTIONAL_SPEC,
    GameType.SPEED_READING_LADDER: SPEED_READING_SPEC,
    GameType.SELF_HELP_FRAMEWORK: SELF_HELP_SPEC,
    GameType.AI_SCENARIO_CONVERSATION: AI_SCENARIO_SPEC,
}


def spec_for(game_type: GameType) -> GameTypeFormSpec:
    return SPECS[game_type]


# ---- form values for pre-populating an edit view -------------------------


def form_values_for(draft) -> Dict[str, str]:
    """Serialize a draft back into the string form-values an HTML form expects."""

    values: Dict[str, str] = {
        "title": draft.title,
        "learning_goal": draft.learning_goal,
        "pass_criteria": draft.pass_criteria,
        "short_description": draft.short_description,
        "difficulty": draft.difficulty.value,
        "estimated_time_minutes": str(draft.estimated_time_minutes),
        "tags_csv": ", ".join(draft.tags),
        "thumbnail_asset_id": draft.thumbnail_asset_id or "",
        "review_mode": draft.moderation.review_mode.value,
        "pass_threshold": str(draft.scoring_rules.pass_threshold),
        "attempts_allowed": str(draft.scoring_rules.attempts_allowed),
    }

    if isinstance(draft, InstructionalMission):
        values.update(
            goal=draft.goal,
            final_result_image_asset_id=draft.final_result_image_asset_id,
            submission_instructions=draft.submission_instructions,
            pass_rule=draft.pass_rule,
            required_proof_type=draft.required_proof_type.value,
            steps_json=_dump_example([asdict(s) for s in draft.steps])
            if draft.steps
            else _dump_example(_INSTRUCTIONAL_STEP_EXAMPLE),
        )
    elif isinstance(draft, SpeedReadingLadder):
        values.update(
            reading_level=draft.reading_level.value,
            timer_seconds=str(draft.timer_seconds),
            target_wpm=str(draft.target_wpm),
            comprehension_threshold=str(draft.comprehension_threshold),
            level_number=str(draft.level_number),
            next_level_id=draft.next_level_id or "",
            promote_on_pass="on" if draft.promote_on_pass else "",
            passages_json=_dump_example([asdict(p) for p in draft.passages])
            if draft.passages
            else _dump_example(_PASSAGES_EXAMPLE),
            questions_json=_dump_example([asdict(q) for q in draft.questions])
            if draft.questions
            else _dump_example(_QUESTIONS_EXAMPLE),
        )
    elif isinstance(draft, SelfHelpFramework):
        values.update(
            framework_name=draft.framework_name,
            lesson_content=draft.lesson_content,
            completion_rule=draft.completion_rule.value,
            concepts_json=_dump_example([asdict(c) for c in draft.key_concepts])
            if draft.key_concepts
            else _dump_example(_CONCEPTS_EXAMPLE),
            reflections_json=_dump_example([asdict(r) for r in draft.reflection_prompts])
            if draft.reflection_prompts
            else _dump_example(_REFLECTIONS_EXAMPLE),
            quiz_json=_dump_example([asdict(q) for q in draft.quiz_questions])
            if draft.quiz_questions
            else _dump_example(_QUIZ_EXAMPLE),
            applications_json=_dump_example([asdict(a) for a in draft.application_tasks])
            if draft.application_tasks
            else _dump_example(_APPLICATION_EXAMPLE),
        )
    elif isinstance(draft, AIScenarioConversation):
        values.update(
            scenario_title=draft.scenario_title,
            scenario_setup=draft.scenario_setup,
            background_info=draft.background_info,
            what_to_figure_out=draft.what_to_figure_out,
            ai_strictness=draft.ai_strictness.value,
            minimum_turns=str(draft.minimum_turns),
            required_targets_hit=str(draft.required_targets_hit),
            follow_up_questions_nl="\n".join(draft.follow_up_questions),
            targets_json=_dump_example([asdict(t) for t in draft.target_reasoning_map])
            if draft.target_reasoning_map
            else _dump_example(_TARGETS_EXAMPLE),
            strong_patterns_json=_dump_example([asdict(p) for p in draft.strong_answer_patterns])
            if draft.strong_answer_patterns
            else _dump_example(_PATTERNS_EXAMPLE),
            weak_patterns_json=_dump_example([asdict(p) for p in draft.weak_answer_patterns])
            if draft.weak_answer_patterns
            else _dump_example(_PATTERNS_EXAMPLE),
            bad_patterns_json=_dump_example([asdict(p) for p in draft.common_bad_answers])
            if draft.common_bad_answers
            else _dump_example(_PATTERNS_EXAMPLE),
            pushback_json=_dump_example([asdict(p) for p in draft.pushback_lines])
            if draft.pushback_lines
            else _dump_example(_PUSHBACK_EXAMPLE),
            hints_json=_dump_example([asdict(h) for h in draft.hint_lines])
            if draft.hint_lines
            else _dump_example(_HINTS_EXAMPLE),
        )

    return values
