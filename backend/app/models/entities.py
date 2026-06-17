import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SeverityLevel(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CameraStatus(str, enum.Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    LEARNING = "learning"
    SURVEILLING = "surveilling"
    ERROR = "error"


class CameraSourceType(str, enum.Enum):
    RTSP = "rtsp"
    WEBCAM = "webcam"
    MOBILE = "mobile"


class EventType(str, enum.Enum):
    PERSON_ENTERED = "person_entered"
    PERSON_EXITED = "person_exited"
    PERSON_LOITERING = "person_loitering"
    UNKNOWN_PERSON = "unknown_person"
    KNOWN_PERSON = "known_person"
    MASKED_PERSON = "masked_person"
    FACE_COVERED = "face_covered"
    MULTIPLE_PERSONS = "multiple_persons"
    TAILGATING = "tailgating"
    ASSET_REMOVED = "asset_removed"
    ASSET_MOVED = "asset_moved"
    ASSET_RETURNED = "asset_returned"
    NEW_ASSET = "new_asset"
    DOOR_OPENED = "door_opened"
    DOOR_CLOSED = "door_closed"
    WINDOW_OPENED = "window_opened"
    LIGHTS_ON = "lights_on"
    LIGHTS_OFF = "lights_off"
    MONITOR_ON = "monitor_on"
    MONITOR_OFF = "monitor_off"
    CAMERA_COVERED = "camera_covered"
    CAMERA_TAMPERED = "camera_tampered"
    CAMERA_DISCONNECTED = "camera_disconnected"
    MOTION_DETECTED = "motion_detected"
    SOUND_ANOMALY = "sound_anomaly"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    baseline_learned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cameras: Mapped[list["Camera"]] = relationship(back_populates="room", cascade="all, delete-orphan")
    objects: Mapped[list["EnvironmentObject"]] = relationship(back_populates="room", cascade="all, delete-orphan")
    events: Mapped[list["Event"]] = relationship(back_populates="room")


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    stream_url: Mapped[str] = mapped_column(String(512))
    source_type: Mapped[str] = mapped_column(String(50), default="rtsp")
    stream_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    status: Mapped[CameraStatus] = mapped_column(Enum(CameraStatus), default=CameraStatus.OFFLINE)
    health_score: Mapped[float] = mapped_column(Float, default=100.0)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    position: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    room: Mapped["Room"] = relationship(back_populates="cameras")
    events: Mapped[list["Event"]] = relationship(back_populates="camera")


class EnvironmentObject(Base):
    __tablename__ = "environment_objects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    label: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100), default="general")
    location: Mapped[dict] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(100), default="present")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    is_tracked: Mapped[bool] = mapped_column(Boolean, default=True)
    admin_labeled: Mapped[bool] = mapped_column(Boolean, default=False)
    relationships: Mapped[dict | None] = mapped_column(JSON)
    baseline_snapshot: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    room: Mapped["Room"] = relationship(back_populates="objects")


class KnownPerson(Base):
    __tablename__ = "known_persons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(100), default="employee")
    embeddings: Mapped[list] = mapped_column(JSON)
    photo_paths: Mapped[list | None] = mapped_column(JSON)
    access_level: Mapped[str] = mapped_column(String(50), default="authorized")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    visit_count: Mapped[int] = mapped_column(Integer, default=0)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    camera_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cameras.id", ondelete="SET NULL"))
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), index=True)
    severity: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel), default=SeverityLevel.INFO)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    event_metadata: Mapped[dict | None] = mapped_column(JSON)
    snapshot_path: Mapped[str | None] = mapped_column(String(512))
    clip_path: Mapped[str | None] = mapped_column(String(512))
    timeline_position: Mapped[float | None] = mapped_column(Float)
    person_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("known_persons.id", ondelete="SET NULL"))
    object_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("environment_objects.id", ondelete="SET NULL"))
    incident_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("incidents.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    room: Mapped["Room"] = relationship(back_populates="events")
    camera: Mapped["Camera | None"] = relationship(back_populates="events")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel))
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="open")
    correlated_events: Mapped[list | None] = mapped_column(JSON)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[EventType] = mapped_column(Enum(EventType))
    min_severity: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM)
    channels: Mapped[list] = mapped_column(JSON)
    sound_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    room_ids: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SurveillanceSession(Base):
    __tablename__ = "surveillance_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    stats: Mapped[dict | None] = mapped_column(JSON)


class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"))
    summary_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    narrative: Mapped[str] = mapped_column(Text)
    stats: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
