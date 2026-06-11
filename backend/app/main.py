import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text

from app.api.router import api_router
from app.config import get_settings
from datetime import datetime, timezone

from app.database import Base, AsyncSessionLocal, engine
from app.models.entities import AlertRule, Camera, CameraStatus, EventType, SeverityLevel, User
from app.security import hash_password
from app.services.frame_buffer import frame_buffer
from app.websocket import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


async def migrate_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE cameras ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'rtsp'"))
        await conn.execute(text("ALTER TABLE cameras ADD COLUMN IF NOT EXISTS stream_token VARCHAR(64)"))
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_cameras_stream_token ON cameras (stream_token) WHERE stream_token IS NOT NULL"
        ))


async def seed_database():
    await migrate_schema()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@sentinel.ai"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@sentinel.ai",
                hashed_password=hash_password("admin123"),
                full_name="System Administrator",
                is_admin=True,
            )
            db.add(admin)

        result = await db.execute(select(AlertRule).limit(1))
        if not result.scalar_one_or_none():
            default_rules = [
                AlertRule(
                    name="Masked Person Alert",
                    event_type=EventType.MASKED_PERSON,
                    min_severity=SeverityLevel.HIGH,
                    channels=["push", "desktop", "sound"],
                    sound_enabled=True,
                ),
                AlertRule(
                    name="Unknown Person Alert",
                    event_type=EventType.UNKNOWN_PERSON,
                    min_severity=SeverityLevel.MEDIUM,
                    channels=["push", "desktop"],
                    sound_enabled=True,
                ),
                AlertRule(
                    name="Asset Removed Alert",
                    event_type=EventType.ASSET_REMOVED,
                    min_severity=SeverityLevel.HIGH,
                    channels=["push", "desktop", "email"],
                    sound_enabled=True,
                ),
                AlertRule(
                    name="Camera Tamper Alert",
                    event_type=EventType.CAMERA_TAMPERED,
                    min_severity=SeverityLevel.CRITICAL,
                    channels=["push", "desktop", "sms"],
                    sound_enabled=True,
                ),
            ]
            for rule in default_rules:
                db.add(rule)

        await db.commit()
    logger.info("Database initialized with seed data")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_database()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Enterprise Edge AI Surveillance & Situational Awareness Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sentinel-backend"}


@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/camera/publish/{stream_token}")
async def websocket_camera_publish(websocket: WebSocket, stream_token: str):
    """Browser/mobile camera publisher — receives JPEG frames."""
    await websocket.accept()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Camera).where(Camera.stream_token == stream_token))
        camera = result.scalar_one_or_none()

    if not camera:
        await websocket.close(code=4001, reason="Invalid stream token")
        return

    camera_id = str(camera.id)
    logger.info("Camera publisher connected: %s (%s)", camera.name, camera.source_type)

    async with AsyncSessionLocal() as db:
        cam = (await db.execute(select(Camera).where(Camera.id == camera.id))).scalar_one()
        cam.status = CameraStatus.ONLINE
        cam.last_heartbeat = datetime.now(timezone.utc)
        await db.commit()

    frame_count = 0
    try:
        while True:
            message = await websocket.receive()
            msg_type = message.get("type", "")

            if msg_type == "websocket.disconnect":
                break

            frame_data = message.get("bytes")
            if frame_data:
                await frame_buffer.store(camera_id, frame_data)
                frame_count += 1
            elif message.get("text"):
                import base64
                import json

                text = message["text"]
                if text == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue
                try:
                    payload = json.loads(text)
                    if payload.get("type") == "frame" and payload.get("data"):
                        data = base64.b64decode(payload["data"])
                        await frame_buffer.store(camera_id, data)
                        frame_count += 1
                except (json.JSONDecodeError, ValueError):
                    pass

            if frame_count % 10 == 0 and frame_count > 0:
                async with AsyncSessionLocal() as db:
                    cam = (await db.execute(select(Camera).where(Camera.id == camera.id))).scalar_one_or_none()
                    if cam:
                        cam.last_heartbeat = datetime.now(timezone.utc)
                        cam.status = CameraStatus.ONLINE
                        await db.commit()

    except WebSocketDisconnect:
        logger.info("Camera publisher disconnected: %s", camera.name)
        async with AsyncSessionLocal() as db:
            cam = (await db.execute(select(Camera).where(Camera.id == camera.id))).scalar_one_or_none()
            if cam and cam.status != CameraStatus.SURVEILLING:
                cam.status = CameraStatus.OFFLINE
                await db.commit()
