import asyncio
import base64
import logging
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.config import get_settings
from app.database import get_db
from app.models.entities import Camera, CameraStatus, EnvironmentObject, KnownPerson, Room, SurveillanceSession, User
from app.schemas.requests import CameraCreate, CameraUpdate, StartLearningRequest, StartSurveillanceRequest
from app.schemas.common import ObjectLocation
from app.schemas.responses import CameraResponse, LearningScanResponse, UnknownObjectPrompt
from app.services.camera_helpers import camera_to_response, prepare_browser_camera
from app.services.frame_buffer import frame_buffer
from app.services.inventory import index_existing, merge_scan_object

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cameras", tags=["Cameras"])
settings = get_settings()


def _base_url(request: Request) -> str:
    if settings.public_base_url:
        return settings.public_base_url.rstrip("/")
    origin = request.headers.get("origin") or request.headers.get("referer", "").rstrip("/")
    if origin and origin.startswith("http"):
        return origin.split("/publish")[0].rstrip("/")
    host = request.headers.get("host", "localhost:3000")
    scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    return f"{scheme}://{host}"


@router.get("", response_model=list[CameraResponse])
async def list_cameras(request: Request, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(select(Camera).order_by(Camera.name))
    cameras = list(result.scalars().all())
    base = _base_url(request)
    responses = [camera_to_response(c, base) for c in cameras]
    await db.flush()
    return responses


@router.post("", response_model=CameraResponse)
async def create_camera(
    req: CameraCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    room = (await db.execute(select(Room).where(Room.id == req.room_id))).scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Room not found")

    source_type = req.source_type or "rtsp"
    stream_url = req.stream_url
    stream_token = None

    if source_type in ("webcam", "mobile"):
        stream_url, stream_token = prepare_browser_camera(source_type)
    elif not stream_url:
        raise HTTPException(400, "Stream URL is required for RTSP cameras")

    camera = Camera(
        room_id=req.room_id,
        name=req.name,
        stream_url=stream_url,
        source_type=source_type,
        stream_token=stream_token,
        position=req.position,
        status=CameraStatus.OFFLINE,
    )
    db.add(camera)
    await db.flush()
    return camera_to_response(camera, _base_url(request))


@router.patch("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: UUID,
    req: CameraUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(404, "Camera not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(camera, field, value)
    await db.flush()
    return camera_to_response(camera, _base_url(request))


@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(404, "Camera not found")
    await db.delete(camera)
    await db.flush()
    return {"status": "deleted", "id": str(camera_id)}


async def _wait_for_frame(camera_id: str, timeout: float = 60.0) -> bytes | None:
    """Wait for a live frame from browser publisher."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if frame_buffer.is_live(camera_id):
            frame = frame_buffer.get(camera_id)
            if frame:
                return frame.data
        await asyncio.sleep(0.5)
    return None


@router.post("/configure/learning", response_model=LearningScanResponse)
async def start_learning(req: StartLearningRequest, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    """Phase 1: Environment learning — scan room and detect objects."""
    result = await db.execute(select(Camera).where(Camera.id == req.camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(404, "Camera not found")

    camera.status = CameraStatus.LEARNING
    await db.flush()

    frame_b64 = None
    if camera.source_type in ("webcam", "mobile"):
        frame_data = await _wait_for_frame(str(camera.id))
        if frame_data:
            frame_b64 = base64.b64encode(frame_data).decode("ascii")
        else:
            raise HTTPException(
                408,
                "No video feed detected. Open the camera publisher link on your phone or laptop first, then retry.",
            )

    scan_payload = {
        "camera_id": str(camera.id),
        "room_id": str(camera.room_id),
        "stream_url": camera.stream_url,
        "source_type": camera.source_type,
        "frame_base64": frame_b64,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{settings.edge_ai_url}/learning/scan", json=scan_payload)
            resp.raise_for_status()
            scan_data = resp.json()
    except httpx.HTTPError:
        from app.services.demo_scanner import run_demo_learning_scan

        scan_data = await run_demo_learning_scan(db, camera)

    if scan_data.get("frame_obstructed"):
        raise HTTPException(
            400,
            scan_data.get("message")
            or "Camera appears blocked or covered. Remove your hand and ensure a clear view of the room.",
        )

    if scan_data.get("detection_mode") == "none":
        raise HTTPException(
            503,
            scan_data.get("message")
            or "Object detection model unavailable. Rebuild the edge-ai container with YOLO enabled.",
        )

    if not scan_data.get("objects"):
        raise HTTPException(
            400,
            scan_data.get("message")
            or "No objects detected in the current camera frame. Point the camera at your desk/room and try again.",
        )

    existing_objs = (
        await db.execute(select(EnvironmentObject).where(EnvironmentObject.room_id == camera.room_id))
    ).scalars().all()
    existing_by_key = index_existing(list(existing_objs))

    unknown_prompts: list[UnknownObjectPrompt] = []
    seen_review_ids: set[UUID] = set()
    added = updated = skipped = 0

    for obj in scan_data.get("objects", []):
        db_obj, action, needs_review = merge_scan_object(existing_by_key, camera.room_id, obj)
        if action == "added":
            db.add(db_obj)
            added += 1
        elif action == "updated":
            updated += 1
        else:
            skipped += 1
        await db.flush()

        if needs_review and db_obj.id not in seen_review_ids:
            seen_review_ids.add(db_obj.id)
            unknown_prompts.append(
                UnknownObjectPrompt(
                    object_id=db_obj.id,
                    label=obj["label"],
                    confidence=float(obj.get("confidence", 0.0)),
                    location=ObjectLocation.model_validate(obj["location"]),
                    snapshot_path=obj.get("snapshot_path"),
                    message=(
                        f"What is this object? (detected as '{obj['label']}' "
                        f"with {obj.get('confidence', 0)}% confidence)"
                    ),
                )
            )

    room = (await db.execute(select(Room).where(Room.id == camera.room_id))).scalar_one()
    room.baseline_learned = True
    if frame_buffer.is_live(str(camera.id)):
        camera.status = CameraStatus.ONLINE
    else:
        camera.status = CameraStatus.OFFLINE
    await db.flush()

    detection_mode = scan_data.get("detection_mode", "yolo")
    scan_msg = scan_data.get("message", "")

    if added == 0 and updated == 0:
        msg = (
            f"Environment already learned — {skipped} known object(s) unchanged."
            if skipped
            else "Scan complete — no new objects detected."
        )
    elif unknown_prompts:
        msg = f"Added {added}, updated {updated}. {len(unknown_prompts)} object(s) need your label."
    else:
        msg = f"Learning complete — {added} new, {updated} updated, {skipped} already known."

    if detection_mode == "yolo":
        msg += " (detected from live camera frame)"

    return LearningScanResponse(
        room_id=camera.room_id,
        camera_id=camera.id,
        objects_detected=len(scan_data.get("objects", [])),
        objects_added=added,
        objects_updated=updated,
        objects_skipped=skipped,
        unknown_objects=unknown_prompts,
        status="learning_complete",
        message=msg,
    )


@router.get("/configure/surveillance/{room_id}")
async def surveillance_status(room_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    """Check if surveillance is active for a room."""
    result = await db.execute(
        select(SurveillanceSession)
        .where(SurveillanceSession.room_id == room_id, SurveillanceSession.is_active.is_(True))
        .order_by(SurveillanceSession.started_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    cameras = (await db.execute(select(Camera).where(Camera.room_id == room_id))).scalars().all()
    feeds_live = sum(1 for c in cameras if frame_buffer.is_live(str(c.id)))
    return {
        "active": session is not None,
        "session_id": str(session.id) if session else None,
        "cameras": len(cameras),
        "feeds_live": feeds_live,
        "surveilling_cameras": sum(1 for c in cameras if c.status == CameraStatus.SURVEILLING),
    }


@router.post("/configure/surveillance")
async def start_surveillance(req: StartSurveillanceRequest, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    """Phase 3: Begin continuous surveillance."""
    room = (await db.execute(select(Room).where(Room.id == req.room_id))).scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Room not found")
    if not room.baseline_learned:
        raise HTTPException(400, "Run environment learning first before activating surveillance.")

    cameras = (await db.execute(select(Camera).where(Camera.room_id == req.room_id))).scalars().all()
    if not cameras:
        raise HTTPException(400, "No cameras configured for this room")

    live_browser = [c for c in cameras if c.source_type in ("webcam", "mobile")]
    if live_browser and not any(frame_buffer.is_live(str(c.id)) for c in live_browser):
        raise HTTPException(
            400,
            "Camera feed is offline. Keep the webcam/mobile publisher open, then activate surveillance.",
        )

    existing = await db.execute(
        select(SurveillanceSession).where(
            SurveillanceSession.room_id == req.room_id,
            SurveillanceSession.is_active.is_(True),
        )
    )
    if existing.scalar_one_or_none():
        return {
            "status": "surveillance_active",
            "message": "Surveillance is already running for this room.",
            "cameras": len(cameras),
        }

    session = SurveillanceSession(room_id=req.room_id, is_active=True)
    db.add(session)

    baseline_objects = []
    objs = (await db.execute(select(EnvironmentObject).where(EnvironmentObject.room_id == req.room_id))).scalars().all()
    if not objs:
        raise HTTPException(400, "No learned assets in this room. Run environment learning first.")
    for o in objs:
        baseline_objects.append({
            "name": o.name,
            "label": o.label,
            "location": o.location,
            "state": o.state,
            "is_tracked": o.is_tracked,
        })

    camera_configs = [
        {"id": str(c.id), "source_type": c.source_type, "stream_url": c.stream_url}
        for c in cameras
    ]

    persons = (await db.execute(select(KnownPerson).where(KnownPerson.is_active.is_(True)))).scalars().all()
    known_persons = [
        {
            "id": str(p.id),
            "name": p.name,
            "role": p.role,
            "embeddings": p.embeddings or [],
        }
        for p in persons
    ]

    for cam in cameras:
        cam.status = CameraStatus.SURVEILLING

    edge_ok = False
    edge_error = None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.edge_ai_url}/surveillance/start",
                json={
                    "room_id": str(req.room_id),
                    "camera_ids": [str(c.id) for c in cameras],
                    "camera_configs": camera_configs,
                    "baseline_objects": baseline_objects,
                    "known_persons": known_persons,
                },
            )
            resp.raise_for_status()
            edge_ok = True
    except httpx.HTTPError as e:
        edge_error = str(e)
        logger.warning("Edge AI surveillance start failed: %s", e)

    await db.flush()
    return {
        "status": "surveillance_active",
        "session_id": str(session.id),
        "cameras": len(cameras),
        "edge_ai_connected": edge_ok,
        "message": (
            f"Surveillance active on {len(cameras)} camera(s). Events will appear in the dashboard."
            if edge_ok
            else f"Surveillance session started but edge AI connection failed: {edge_error}"
        ),
    }
