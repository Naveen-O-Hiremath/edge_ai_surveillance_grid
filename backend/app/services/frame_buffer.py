"""In-memory latest-frame store for browser/mobile camera publishers."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import asyncio


@dataclass
class CameraFrame:
    camera_id: str
    data: bytes
    content_type: str = "image/jpeg"
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    frame_count: int = 0


class FrameBuffer:
    def __init__(self):
        self._frames: dict[str, CameraFrame] = {}
        self._lock = asyncio.Lock()
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    async def store(self, camera_id: str, data: bytes, content_type: str = "image/jpeg") -> None:
        async with self._lock:
            existing = self._frames.get(camera_id)
            count = (existing.frame_count + 1) if existing else 1
            frame = CameraFrame(
                camera_id=camera_id,
                data=data,
                content_type=content_type,
                frame_count=count,
            )
            self._frames[camera_id] = frame

        for queue in self._subscribers.get(camera_id, []):
            try:
                queue.put_nowait(frame)
            except asyncio.QueueFull:
                pass

    def get(self, camera_id: str) -> CameraFrame | None:
        return self._frames.get(camera_id)

    def is_live(self, camera_id: str, max_age_seconds: float = 10.0) -> bool:
        frame = self._frames.get(camera_id)
        if not frame:
            return False
        age = (datetime.now(timezone.utc) - frame.received_at).total_seconds()
        return age <= max_age_seconds

    def status(self, camera_id: str) -> dict:
        frame = self._frames.get(camera_id)
        if not frame:
            return {"connected": False, "last_frame_at": None, "frame_count": 0}
        return {
            "connected": self.is_live(camera_id),
            "last_frame_at": frame.received_at.isoformat(),
            "frame_count": frame.frame_count,
        }


frame_buffer = FrameBuffer()
