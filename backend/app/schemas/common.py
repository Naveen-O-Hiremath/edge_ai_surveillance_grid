from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.entities import CameraStatus, EventType, SeverityLevel


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class ObjectLocation(BaseModel):
    bbox: BoundingBox
    zone: str | None = None
    relative_to: str | None = None


class ThreatAssessment(BaseModel):
    severity: SeverityLevel
    confidence: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)


class EventCreate(BaseModel):
    room_id: UUID
    camera_id: UUID | None = None
    event_type: EventType
    title: str
    description: str | None = None
    confidence: float = 0.0
    metadata: dict | None = None
    snapshot_path: str | None = None
    clip_path: str | None = None
    timeline_position: float | None = None
    person_id: UUID | None = None
    object_id: UUID | None = None


class TimestampMixin(BaseModel):
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
