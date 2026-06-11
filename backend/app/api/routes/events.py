from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.entities import Event, User
from app.schemas.common import EventCreate
from app.schemas.responses import EventResponse, IncidentResponse, NLQueryResponse
from app.schemas.requests import NLQueryRequest
from app.services.ai_summary import ai_summary_service
from app.services.event_pipeline import event_pipeline
from app.models.entities import Incident

router = APIRouter(tags=["Events"])


@router.get("/events", response_model=list[EventResponse])
async def list_events(
    room_id: UUID | None = None,
    severity: str | None = None,
    event_type: str | None = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = select(Event).order_by(Event.created_at.desc()).limit(limit).offset(offset)
    if room_id:
        q = q.where(Event.room_id == room_id)
    if severity:
        q = q.where(Event.severity == severity)
    if event_type:
        q = q.where(Event.event_type == event_type)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/events/ingest", response_model=EventResponse)
async def ingest_event(data: EventCreate, db: AsyncSession = Depends(get_db)):
    """Edge AI event ingestion endpoint."""
    event = await event_pipeline.ingest(db, data)
    return event


@router.get("/incidents", response_model=list[IncidentResponse])
async def list_incidents(
    status: str | None = "open",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = select(Incident).order_by(Incident.started_at.desc())
    if status:
        q = q.where(Incident.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/search", response_model=NLQueryResponse)
async def natural_language_search(
    req: NLQueryRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    answer, events = await ai_summary_service.natural_language_query(db, req.query, req.room_id)
    return NLQueryResponse(query=req.query, answer=answer, matching_events=events)
