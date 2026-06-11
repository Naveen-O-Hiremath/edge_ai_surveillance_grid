import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from app.learning.scanner import EnvironmentScanner
from app.pipeline.surveillance import surveillance_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scanner = EnvironmentScanner()


class ScanRequest(BaseModel):
    camera_id: str
    room_id: str
    stream_url: str | None = None
    source_type: str = "rtsp"
    frame_base64: str | None = None


class CameraConfig(BaseModel):
    id: str
    source_type: str = "rtsp"
    stream_url: str = ""


class KnownPersonConfig(BaseModel):
    id: str
    name: str
    role: str = "employee"
    embeddings: list[list[float]] | None = None


class SurveillanceRequest(BaseModel):
    room_id: str
    camera_ids: list[str]
    camera_configs: list[CameraConfig] | None = None
    baseline_objects: list[dict] | None = None
    known_persons: list[KnownPersonConfig] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Edge AI service started")
    yield
    for room_id in list(surveillance_engine._active_sessions.keys()):
        await surveillance_engine.stop(room_id)


app = FastAPI(
    title="Sentinel Edge AI",
    description="Edge processing for object detection, tracking, and surveillance",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sentinel-edge-ai"}


@app.post("/learning/scan")
async def learning_scan(req: ScanRequest):
    """Phase 1: Scan environment and build baseline inventory."""
    from app.pipeline.frame_source import get_frame

    frame = await get_frame(
        req.camera_id,
        req.stream_url or "",
        req.source_type,
        req.frame_base64,
    )
    result = scanner.scan(frame)
    return {
        "camera_id": req.camera_id,
        "room_id": req.room_id,
        "objects": result["objects"],
        "unknown_objects": result["unknown_objects"],
        "status": "scan_complete",
        "frame_obstructed": result.get("frame_obstructed", False),
        "detection_mode": result.get("detection_mode", "none"),
        "message": result.get("message", ""),
    }


@app.post("/surveillance/start")
async def start_surveillance(req: SurveillanceRequest):
    """Phase 3: Start continuous surveillance."""
    if req.baseline_objects:
        surveillance_engine.set_baseline(req.room_id, req.baseline_objects)
    configs = {c.id: c.model_dump() for c in (req.camera_configs or [])}
    known = [p.model_dump() for p in (req.known_persons or [])]
    await surveillance_engine.start(req.room_id, req.camera_ids, configs, known)
    return {"status": "active", "room_id": req.room_id, "cameras": len(req.camera_ids)}


@app.post("/surveillance/stop")
async def stop_surveillance(room_id: str):
    await surveillance_engine.stop(room_id)
    return {"status": "stopped", "room_id": room_id}
