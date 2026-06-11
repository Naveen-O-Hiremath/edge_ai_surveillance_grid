"""Public camera publisher endpoints (token-authenticated, no login)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entities import Camera
from app.services.frame_buffer import frame_buffer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/publish", tags=["Camera Publisher"])


def _client_host(request: Request) -> str:
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:3000"
    return host.split(":")[0]


@router.get("/setup")
async def publish_setup(request: Request):
    """Tell the browser where to send frames (direct backend :8000, not nginx)."""
    host = _client_host(request)
    scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    frontend_port = request.headers.get("x-forwarded-port") or "3000"
    return {
        "frontend_base": f"{scheme}://{host}:{frontend_port}",
        "backend_base": f"{scheme}://{host}:8000",
        "api_base": f"{scheme}://{host}:8000/api/v1",
        "ws_base": f"{'wss' if scheme == 'https' else 'ws'}://{host}:8000",
        "client_host": host,
    }


async def _camera_by_token(db: AsyncSession, stream_token: str) -> Camera:
    result = await db.execute(select(Camera).where(Camera.stream_token == stream_token))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(404, "Invalid or expired stream token")
    return camera


@router.get("/{stream_token}/info")
async def publish_info(stream_token: str, db: AsyncSession = Depends(get_db)):
    camera = await _camera_by_token(db, stream_token)
    return {
        "camera_id": str(camera.id),
        "name": camera.name,
        "source_type": camera.source_type,
        "publish_path": f"/publish/{camera.source_type}/{stream_token}",
    }


@router.post("/{stream_token}/frame")
async def upload_frame(
    stream_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive JPEG frames from browser/mobile camera (raw body)."""
    camera = await _camera_by_token(db, stream_token)
    camera_id = str(camera.id)

    data = await request.body()
    if len(data) < 100:
        raise HTTPException(400, f"Frame too small ({len(data)} bytes)")

    await frame_buffer.store(camera_id, data)

    logger.debug("Frame stored for camera %s (%d bytes)", camera.name, len(data))
    return {"status": "ok", "bytes": len(data), "camera_id": camera_id}


@router.get("/{stream_token}/status")
async def publish_status(stream_token: str, db: AsyncSession = Depends(get_db)):
    camera = await _camera_by_token(db, stream_token)
    st = frame_buffer.status(str(camera.id))
    return {"camera_id": str(camera.id), "name": camera.name, **st}
