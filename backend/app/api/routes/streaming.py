import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.entities import Camera, CameraStatus, User
from app.services.frame_buffer import frame_buffer

router = APIRouter(prefix="/cameras", tags=["Camera Streaming"])


@router.get("/{camera_id}/snapshot")
async def get_snapshot(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(404, "Camera not found")

    frame = frame_buffer.get(str(camera_id))
    if not frame:
        raise HTTPException(404, "No live frame available — start the camera publisher first")

    return Response(content=frame.data, media_type=frame.content_type)


@router.get("/{camera_id}/stream-status")
async def stream_status(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(404, "Camera not found")

    status = frame_buffer.status(str(camera_id))
    return {
        "camera_id": str(camera_id),
        "source_type": camera.source_type,
        "camera_status": camera.status.value,
        **status,
    }


@router.post("/{camera_id}/regenerate-token")
async def regenerate_stream_token(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(404, "Camera not found")
    if camera.source_type not in ("webcam", "mobile"):
        raise HTTPException(400, "Only browser cameras use stream tokens")

    camera.stream_token = secrets.token_urlsafe(24)
    await db.flush()
    return {"stream_token": camera.stream_token}


# Internal endpoint for edge-ai (docker network only)
internal_router = APIRouter(prefix="/internal/cameras", tags=["Internal"])


@internal_router.get("/{camera_id}/frame")
async def internal_get_frame(camera_id: UUID, db: AsyncSession = Depends(get_db)):
    frame = frame_buffer.get(str(camera_id))
    if not frame:
        raise HTTPException(404, "No frame")
    return Response(content=frame.data, media_type=frame.content_type)
