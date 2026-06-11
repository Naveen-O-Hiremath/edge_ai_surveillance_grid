from uuid import UUID

from pydantic import BaseModel, Field

from app.models.entities import CameraStatus, EventType, SeverityLevel


class LoginRequest(BaseModel):
    email: str
    password: str


class RoomCreate(BaseModel):
    name: str
    description: str | None = None


class RoomUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CameraCreate(BaseModel):
    room_id: UUID
    name: str
    stream_url: str = ""
    source_type: str = "rtsp"
    position: dict | None = None


class CameraUpdate(BaseModel):
    name: str | None = None
    room_id: UUID | None = None
    stream_url: str | None = None
    source_type: str | None = None
    status: CameraStatus | None = None
    position: dict | None = None


class EnvironmentObjectUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    state: str | None = None
    is_tracked: bool | None = None


class KnownPersonUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    access_level: str | None = None


class LabelUnknownObjectRequest(BaseModel):
    name: str
    category: str = "general"
    is_tracked: bool = True


class KnownPersonCreate(BaseModel):
    name: str
    role: str = "employee"
    access_level: str = "authorized"


class AlertRuleCreate(BaseModel):
    name: str
    event_type: EventType
    min_severity: SeverityLevel = SeverityLevel.MEDIUM
    channels: list[str] = Field(default_factory=lambda: ["push", "desktop"])
    sound_enabled: bool = True
    room_ids: list[UUID] | None = None


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    min_severity: SeverityLevel | None = None
    channels: list[str] | None = None
    sound_enabled: bool | None = None
    is_active: bool | None = None
    room_ids: list[UUID] | None = None


class StartLearningRequest(BaseModel):
    camera_id: UUID


class StartSurveillanceRequest(BaseModel):
    room_id: UUID


class NLQueryRequest(BaseModel):
    query: str
    room_id: UUID | None = None


class SummaryRequest(BaseModel):
    room_id: UUID | None = None
    period: str = "daily"
