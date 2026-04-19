"""Media assets — screenshots, final-result images, thumbnails, recordings."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class MediaKind(str, Enum):
    SCREENSHOT = "screenshot"
    FINAL_RESULT = "final_result"
    THUMBNAIL = "thumbnail"
    SCREEN_RECORDING = "screen_recording"
    AUDIO = "audio"
    OTHER = "other"


@dataclass
class MediaAsset:
    kind: MediaKind
    url: str
    mime_type: str
    byte_size: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    alt_text: Optional[str] = None
    id: str = field(default_factory=lambda: uuid4().hex)
    uploaded_by: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
