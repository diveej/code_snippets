"""Question bank — reusable quiz and comprehension items.

Used by Speed Reading Ladder (comprehension) and Self-Help Framework (quiz).
"""

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import uuid4

from game_content_system.core.enums import Difficulty


@dataclass
class BankItem:
    prompt: str
    choices: List[str]
    correct_index: int
    explanation: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    difficulty: Difficulty = Difficulty.BEGINNER
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass
class QuestionBank:
    name: str
    items: List[BankItem] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid4().hex)

    def filter_by_tag(self, tag: str) -> List[BankItem]:
        return [i for i in self.items if tag in i.tags]
