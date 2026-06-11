from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.entities import CameraStatus, EventType, SeverityLevel
from app.schemas.common import ObjectLocation


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoomResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    baseline_learned: bool
    created_at: datetime
    camera_count: int = 0
    object_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CameraResponse(BaseModel):
    id: UUID
    room_id: UUID
    name: str
    stream_url: str
    source_type: str = "rtsp"
    stream_token: str | None = None
    publish_path: str | None = None
    publish_url: str | None = None
    status: CameraStatus
    health_score: float
    last_heartbeat: datetime | None
    position: dict | None
    is_streaming: bool = False

    model_config = ConfigDict(from_attributes=True)


class EnvironmentObjectResponse(BaseModel):
    id: UUID
    room_id: UUID
    name: str
    label: str
    category: str
    location: dict
    state: str
    confidence: float
    is_tracked: bool
    admin_labeled: bool
    relationships: dict | None

    model_config = ConfigDict(from_attributes=True)


class UnknownObjectPrompt(BaseModel):
    object_id: UUID
    label: str
    confidence: float
    location: ObjectLocation
    snapshot_path: str | None
    message: str


class LearningScanResponse(BaseModel):
    room_id: UUID
    camera_id: UUID
    objects_detected: int
    objects_added: int = 0
    objects_updated: int = 0
    objects_skipped: int = 0
    unknown_objects: list[UnknownObjectPrompt]
    status: str
    message: str = ""


class KnownPersonResponse(BaseModel):
    id: UUID
    name: str
    role: str
    access_level: str
    is_active: bool
    visit_count: int
    last_seen: datetime | None
    embedding_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class EventResponse(BaseModel):
    id: UUID
    room_id: UUID
    camera_id: UUID | None
    event_type: EventType
    severity: SeverityLevel
    confidence: float
    risk_score: float
    title: str
    description: str | None
    event_metadata: dict | None = None
    snapshot_path: str | None
    clip_path: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentResponse(BaseModel):
    id: UUID
    room_id: UUID
    title: str
    description: str | None
    severity: SeverityLevel
    risk_score: float
    status: str
    correlated_events: list | None
    ai_summary: str | None
    started_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AlertRuleResponse(BaseModel):
    id: UUID
    name: str
    event_type: EventType
    min_severity: SeverityLevel
    channels: list
    sound_enabled: bool
    is_active: bool
    room_ids: list | None

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    total_cameras: int
    online_cameras: int
    active_threats: int
    events_today: int
    unknown_visitors_today: int
    asset_alerts_today: int
    open_incidents: int
    risk_score_avg: float


class TimelinePoint(BaseModel):
    hour: int
    count: int
    severity_breakdown: dict[str, int]


class HeatmapCell(BaseModel):
    x: int
    y: int
    intensity: float


class AnalyticsResponse(BaseModel):
    stats: DashboardStats
    timeline: list[TimelinePoint]
    event_distribution: dict[str, int]
    severity_distribution: dict[str, int]
    heatmap: list[HeatmapCell]
    top_threats: list[EventResponse]


class SummaryResponse(BaseModel):
    period: str
    room_id: UUID | None
    narrative: str
    stats: dict
    generated_at: datetime


class NLQueryResponse(BaseModel):
    query: str
    answer: str
    matching_events: list[EventResponse]
