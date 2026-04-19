"""Game Content System — admin portal + data model for 4 game types.

Game types:
    1. Instructional Mission
    2. Speed Reading Ladder
    3. Self-Help Framework Builder
    4. AI Scenario Conversation
"""

from game_content_system.core.enums import (
    GameType,
    Difficulty,
    Status,
    SubmissionType,
    ProofType,
    CompletionRule,
    AIStrictness,
)
from game_content_system.core.base import ContentBase, ScoringRules, ModerationSettings
from game_content_system.core.validation import ValidationError, ValidationResult
from game_content_system.admin.registry import GameTypeRegistry, registry

__all__ = [
    "GameType",
    "Difficulty",
    "Status",
    "SubmissionType",
    "ProofType",
    "CompletionRule",
    "AIStrictness",
    "ContentBase",
    "ScoringRules",
    "ModerationSettings",
    "ValidationError",
    "ValidationResult",
    "GameTypeRegistry",
    "registry",
]
