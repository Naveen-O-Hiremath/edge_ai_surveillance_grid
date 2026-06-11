"""Central event ingestion pipeline."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Event, EventType, KnownPerson
from app.schemas.common import EventCreate
from app.services.alert_service import alert_service
from app.services.event_correlator import event_correlator
from app.services.threat_engine import threat_engine


class EventPipeline:
    async def ingest(self, db: AsyncSession, data: EventCreate) -> Event:
        assessment = threat_engine.assess(
            data.event_type,
            data.confidence,
            context=(data.metadata or {}).get("context"),
        )

        event = Event(
            room_id=data.room_id,
            camera_id=data.camera_id,
            event_type=data.event_type,
            severity=assessment.severity,
            confidence=assessment.confidence,
            risk_score=assessment.risk_score,
            title=data.title,
            description=data.description,
            event_metadata=data.metadata,
            snapshot_path=data.snapshot_path,
            clip_path=data.clip_path,
            timeline_position=data.timeline_position,
            person_id=data.person_id,
            object_id=data.object_id,
        )
        db.add(event)
        await db.flush()

        if data.event_type == EventType.KNOWN_PERSON and data.person_id:
            if not (data.metadata or {}).get("activity") == "phone_use":
                result = await db.execute(select(KnownPerson).where(KnownPerson.id == data.person_id))
                person = result.scalar_one_or_none()
                if person:
                    person.visit_count += 1
                    person.last_seen = datetime.now(timezone.utc)
                    await db.flush()

        incident = await event_correlator.process_event(db, event)
        if incident:
            event.event_metadata = {**(event.event_metadata or {}), "incident_id": str(incident.id)}

        await alert_service.dispatch_for_event(db, event)

        try:
            from app.websocket import manager

            await manager.broadcast({"type": "event", "data": {
                "id": str(event.id),
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "title": event.title,
                "risk_score": event.risk_score,
                "created_at": event.created_at.isoformat(),
            }})
        except Exception:
            pass

        return event


event_pipeline = EventPipeline()
