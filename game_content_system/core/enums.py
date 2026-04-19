"""Enums shared across the content system."""

from enum import Enum


class GameType(str, Enum):
    INSTRUCTIONAL_MISSION = "instructional_mission"
    SPEED_READING_LADDER = "speed_reading_ladder"
    SELF_HELP_FRAMEWORK = "self_help_framework"
    AI_SCENARIO_CONVERSATION = "ai_scenario_conversation"


class Difficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Status(str, Enum):
    DRAFT = "draft"
    QA = "qa"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SubmissionType(str, Enum):
    SCREENSHOT = "screenshot"
    SCREEN_RECORDING = "screen_recording"
    TEXT = "text"
    QUIZ = "quiz"
    REFLECTION = "reflection"
    APPLICATION = "application"
    CONVERSATION = "conversation"


class ProofType(str, Enum):
    SCREENSHOT = "screenshot"
    SCREEN_RECORDING = "screen_recording"
    TEXT = "text"


class CompletionRule(str, Enum):
    QUIZ_ONLY = "quiz_only"
    REFLECTION_ONLY = "reflection_only"
    APPLICATION_ONLY = "application_only"
    MIXED = "mixed"


class AIStrictness(str, Enum):
    LENIENT = "lenient"
    BALANCED = "balanced"
    STRICT = "strict"


class ReviewMode(str, Enum):
    MANUAL = "manual"
    AUTO_PASS = "auto_pass"


class ReadingLevel(str, Enum):
    ELEMENTARY = "elementary"
    MIDDLE = "middle"
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"
    ADULT = "adult"
