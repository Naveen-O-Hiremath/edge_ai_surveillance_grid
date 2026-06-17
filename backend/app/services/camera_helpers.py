import secrets

from app.models.entities import Camera
from app.schemas.responses import CameraResponse
from app.services.camera_health import is_camera_streaming, sync_camera_from_frames


def build_publish_path(source_type: str, token: str) -> str:
    return f"/publish/{source_type}/{token}"


def camera_to_response(camera: Camera, base_url: str = "", *, sync: bool = True) -> CameraResponse:
    if sync:
        sync_camera_from_frames(camera)

    is_streaming = is_camera_streaming(camera)
    publish_path = None
    publish_url = None
    if camera.stream_token and camera.source_type in ("webcam", "mobile"):
        publish_path = build_publish_path(camera.source_type, camera.stream_token)
        publish_url = f"{base_url}{publish_path}" if base_url else publish_path

    return CameraResponse(
        id=camera.id,
        room_id=camera.room_id,
        name=camera.name,
        stream_url=camera.stream_url,
        source_type=camera.source_type,
        stream_token=camera.stream_token,
        publish_path=publish_path,
        publish_url=publish_url,
        status=camera.status,
        health_score=round(camera.health_score, 1),
        last_heartbeat=camera.last_heartbeat,
        position=camera.position,
        is_streaming=is_streaming,
    )


def prepare_browser_camera(source_type: str) -> tuple[str, str]:
    token = secrets.token_urlsafe(24)
    stream_url = f"browser://{source_type}"
    return stream_url, token
