"""Correlates related events into incidents (e.g., theft chains)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Event, EventType, Incident, SeverityLevel

CORRELATION_WINDOW_SECONDS = 300

THEFT_CHAIN = [
    EventType.UNKNOWN_PERSON,
    EventType.MASKED_PERSON,
    EventType.ASSET_REMOVED,
    EventType.PERSON_EXITED,
]

INTRUSION_CHAIN = [
    EventType.DOOR_OPENED,
    EventType.UNKNOWN_PERSON,
    EventType.PERSON_LOITERING,
]


class EventCorrelator:
    async def process_event(self, db: AsyncSession, event: Event) -> Incident | None:
        recent = await self._get_recent_events(db, event.room_id, seconds=CORRELATION_WINDOW_SECONDS)
        recent_types = [e.event_type for e in recent] + [event.event_type]

        if self._matches_chain(recent_types, THEFT_CHAIN):
            return await self._create_incident(
                db,
                room_id=event.room_id,
                title="Potential Theft Event",
                description="Correlated sequence: unauthorized person entered, asset removed, person exited.",
                severity=SeverityLevel.CRITICAL,
                risk_score=92.0,
                event_ids=[e.id for e in recent] + [event.id],
            )

        if self._matches_chain(recent_types, INTRUSION_CHAIN):
            return await self._create_incident(
                db,
                room_id=event.room_id,
                title="Potential Intrusion",
                description="Correlated sequence: door opened, unknown person detected, loitering observed.",
                severity=SeverityLevel.HIGH,
                risk_score=78.0,
                event_ids=[e.id for e in recent] + [event.id],
            )

        if event.event_type == EventType.MASKED_PERSON:
            return await self._create_incident(
                db,
                room_id=event.room_id,
                title="Masked Individual Detected",
                description=event.description or "A masked or face-covered individual was detected.",
                severity=SeverityLevel.CRITICAL,
                risk_score=95.0,
                event_ids=[event.id],
            )

        return None

    async def _get_recent_events(
        self, db: AsyncSession, room_id: UUID, seconds: int
    ) -> list[Event]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        result = await db.execute(
            select(Event)
            .where(Event.room_id == room_id, Event.created_at >= cutoff)
            .order_by(Event.created_at.desc())
            .limit(20)
        )
        return list(result.scalars().all())

    def _matches_chain(self, events: list[EventType], chain: list[EventType]) -> bool:
        chain_idx = 0
        for et in events:
            if et == chain[chain_idx]:
                chain_idx += 1
                if chain_idx == len(chain):
                    return True
        return False

    async def _create_incident(
        self,
        db: AsyncSession,
        room_id: UUID,
        title: str,
        description: str,
        severity: SeverityLevel,
        risk_score: float,
        event_ids: list[UUID],
    ) -> Incident:
        incident = Incident(
            room_id=room_id,
            title=title,
            description=description,
            severity=severity,
            risk_score=risk_score,
            correlated_events=[str(eid) for eid in event_ids],
            status="open",
        )
        db.add(incident)
        await db.flush()

        for eid in event_ids:
            result = await db.execute(select(Event).where(Event.id == eid))
            ev = result.scalar_one_or_none()
            if ev:
                ev.incident_id = incident.id

        return incident


event_correlator = EventCorrelator()
