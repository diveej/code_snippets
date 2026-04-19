"""Game-type registry — drives the "choose game type then load the right form"
admin flow from Phase 3.

The admin portal calls `registry.schema_for(game_type)` to instantiate an
empty draft of the correct subclass, then hands it to the dynamic form.
`registry.publish(content)` runs validation and flips status to PUBLISHED.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, List, Type

from game_content_system.core.base import ContentBase
from game_content_system.core.enums import GameType, Status
from game_content_system.core.validation import ValidationError, ValidationResult
from game_content_system.game_types.ai_scenario import AIScenarioConversation
from game_content_system.game_types.instructional import InstructionalMission
from game_content_system.game_types.self_help import SelfHelpFramework
from game_content_system.game_types.speed_reading import SpeedReadingLadder


@dataclass
class GameTypeEntry:
    game_type: GameType
    label: str
    description: str
    schema: Type[ContentBase]


@dataclass
class GameTypeRegistry:
    _entries: Dict[GameType, GameTypeEntry] = field(default_factory=dict)

    def register(
        self,
        game_type: GameType,
        label: str,
        description: str,
        schema: Type[ContentBase],
    ) -> None:
        self._entries[game_type] = GameTypeEntry(
            game_type=game_type,
            label=label,
            description=description,
            schema=schema,
        )

    def list(self) -> List[GameTypeEntry]:
        return list(self._entries.values())

    def schema_for(self, game_type: GameType) -> Type[ContentBase]:
        if game_type not in self._entries:
            raise KeyError(f"no registered schema for {game_type}")
        return self._entries[game_type].schema

    def new_draft(self, game_type: GameType, **kwargs) -> ContentBase:
        """Instantiate an empty draft of the right subclass (admin step 2 & 3)."""

        schema_cls = self.schema_for(game_type)
        return schema_cls(**kwargs)

    def validate(self, content: ContentBase) -> ValidationResult:
        validate_fn: Callable[[], ValidationResult] = getattr(content, "validate")
        return validate_fn()

    def publish(self, content: ContentBase) -> ContentBase:
        """Run full validation, then flip DRAFT/QA -> PUBLISHED.

        Raises ValidationError if the content is not publishable — this is
        what enforces Phase 5's "valid game" rules.
        """

        result = self.validate(content)
        result.raise_if_failed()
        content.status = Status.PUBLISHED
        content.published_at = datetime.now(timezone.utc)
        content.updated_at = datetime.now(timezone.utc)
        return content

    def archive(self, content: ContentBase) -> ContentBase:
        content.status = Status.ARCHIVED
        content.updated_at = datetime.now(timezone.utc)
        return content

    def iter_publishable(self, contents: Iterable[ContentBase]) -> Iterable[ContentBase]:
        for c in contents:
            if self.validate(c).ok:
                yield c


registry = GameTypeRegistry()
registry.register(
    GameType.INSTRUCTIONAL_MISSION,
    label="Instructional Mission",
    description="Screenshots + steps + a final target result the student must reproduce.",
    schema=InstructionalMission,
)
registry.register(
    GameType.SPEED_READING_LADDER,
    label="Speed Reading Ladder",
    description="Timed reading with comprehension checks; pass requires both speed and understanding.",
    schema=SpeedReadingLadder,
)
registry.register(
    GameType.SELF_HELP_FRAMEWORK,
    label="Self-Help Framework Builder",
    description="Read an idea, then show you understand it via reflection, quiz, or application.",
    schema=SelfHelpFramework,
)
registry.register(
    GameType.AI_SCENARIO_CONVERSATION,
    label="AI Scenario Conversation",
    description="Guided thinking game; the AI pushes back and makes the student defend their reasoning.",
    schema=AIScenarioConversation,
)
