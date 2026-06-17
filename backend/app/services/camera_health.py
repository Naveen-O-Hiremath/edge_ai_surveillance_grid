"""Derive camera health and streaming state from real frame data — never guess."""

from datetime import datetime, timezone

from app.models.entities import Camera, CameraStatus
from app.services.frame_buffer import frame_buffer

BROWSER_SOURCES = frozenset({"webcam", "mobile"})
LIVE_MAX_AGE_SEC = 10.0


def is_camera_streaming(camera: Camera) -> bool:
    if camera.source_type not in BROWSER_SOURCES:
        return False
    return frame_buffer.is_live(str(camera.id), max_age_seconds=LIVE_MAX_AGE_SEC)


def compute_health_score(camera_id: str) -> float:
    frame = frame_buffer.get(camera_id)
    if not frame:
        return 0.0
    age = (datetime.now(timezone.utc) - frame.received_at).total_seconds()
    if age > LIVE_MAX_AGE_SEC:
        return 0.0
    if age <= 2.0:
        return 100.0
    if age <= 5.0:
        return 85.0
    return max(10.0, 100.0 - age * 8.0)


def sync_camera_from_frames(camera: Camera) -> bool:
    """
    Update camera health_score and heartbeat from the frame buffer.
    Returns True when the camera is actively receiving frames.
    """
    cid = str(camera.id)
    if camera.source_type not in BROWSER_SOURCES:
        camera.health_score = 0.0
        return False

    live = is_camera_streaming(camera)
    camera.health_score = compute_health_score(cid) if live else 0.0

    frame = frame_buffer.get(cid)
    if live and frame:
        camera.last_heartbeat = frame.received_at
        if camera.status == CameraStatus.OFFLINE:
            camera.status = CameraStatus.ONLINE
    elif camera.status in (CameraStatus.ONLINE, CameraStatus.LEARNING):
        camera.status = CameraStatus.OFFLINE

    return live
