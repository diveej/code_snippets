"""In-memory content store for the admin portal MVP.

Swap this for a real DB later — routes only depend on the three methods
below.
"""

from threading import RLock
from typing import Dict, List, Optional

from game_content_system.core.base import ContentBase


class ContentStore:
    def __init__(self) -> None:
        self._items: Dict[str, ContentBase] = {}
        self._lock = RLock()

    def save(self, content: ContentBase) -> ContentBase:
        with self._lock:
            self._items[content.id] = content
            return content

    def get(self, content_id: str) -> Optional[ContentBase]:
        with self._lock:
            return self._items.get(content_id)

    def list(self) -> List[ContentBase]:
        with self._lock:
            return sorted(
                self._items.values(),
                key=lambda c: c.updated_at,
                reverse=True,
            )

    def delete(self, content_id: str) -> None:
        with self._lock:
            self._items.pop(content_id, None)
