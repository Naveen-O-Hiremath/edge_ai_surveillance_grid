"""AI-powered daily/weekly incident summarization."""

from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import DailySummary, Event, EventType, Incident, KnownPerson, SeverityLevel


class AISummaryService:
    async def generate_daily_summary(
        self, db: AsyncSession, room_id: UUID | None = None
    ) -> DailySummary:
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        events = await self._fetch_events(db, start, now, room_id)
        incidents = await self._fetch_incidents(db, start, now, room_id)

        stats = self._compute_stats(events, incidents)
        narrative = self._generate_narrative(events, incidents, stats, start, now)

        summary = DailySummary(
            room_id=room_id,
            summary_date=start,
            narrative=narrative,
            stats=stats,
        )
        db.add(summary)
        await db.flush()
        return summary

    async def _fetch_events(
        self, db: AsyncSession, start: datetime, end: datetime, room_id: UUID | None
    ) -> list[Event]:
        q = select(Event).where(Event.created_at >= start, Event.created_at <= end)
        if room_id:
            q = q.where(Event.room_id == room_id)
        result = await db.execute(q.order_by(Event.created_at))
        return list(result.scalars().all())

    async def _fetch_incidents(
        self, db: AsyncSession, start: datetime, end: datetime, room_id: UUID | None
    ) -> list[Incident]:
        q = select(Incident).where(Incident.started_at >= start, Incident.started_at <= end)
        if room_id:
            q = q.where(Incident.room_id == room_id)
        result = await db.execute(q)
        return list(result.scalars().all())

    def _compute_stats(self, events: list[Event], incidents: list[Incident]) -> dict:
        type_counts = Counter(e.event_type.value for e in events)
        severity_counts = Counter(e.severity.value for e in events)

        entries = sum(
            1 for e in events if e.event_type in (EventType.PERSON_ENTERED, EventType.KNOWN_PERSON)
        )
        exits = sum(1 for e in events if e.event_type == EventType.PERSON_EXITED)
        unknown = sum(1 for e in events if e.event_type == EventType.UNKNOWN_PERSON)
        masked = sum(1 for e in events if e.event_type == EventType.MASKED_PERSON)
        asset_events = sum(
            1
            for e in events
            if e.event_type
            in (EventType.ASSET_REMOVED, EventType.ASSET_MOVED, EventType.ASSET_RETURNED)
        )

        return {
            "total_events": len(events),
            "personnel_entries": entries,
            "personnel_exits": exits,
            "unknown_visitors": unknown,
            "masked_detections": masked,
            "asset_events": asset_events,
            "incidents": len(incidents),
            "critical_events": severity_counts.get(SeverityLevel.CRITICAL.value, 0),
            "event_types": dict(type_counts),
            "severity_breakdown": dict(severity_counts),
            "avg_risk_score": round(sum(e.risk_score for e in events) / max(len(events), 1), 1),
        }

    def _generate_narrative(
        self,
        events: list[Event],
        incidents: list[Incident],
        stats: dict,
        start: datetime,
        end: datetime,
    ) -> str:
        period = f"{start.strftime('%I:%M %p')} and {end.strftime('%I:%M %p')}"
        parts = [
            f"Security Summary for {start.strftime('%B %d, %Y')}.",
            f"Between {period}, {stats['personnel_entries']} personnel entries "
            f"and {stats['personnel_exits']} exits were recorded across monitored areas.",
        ]

        if stats["unknown_visitors"]:
            unknown_events = [e for e in events if e.event_type == EventType.UNKNOWN_PERSON]
            if unknown_events:
                first = unknown_events[0]
                parts.append(
                    f"{stats['unknown_visitors']} unknown individual(s) detected. "
                    f"First occurrence at {first.created_at.strftime('%I:%M %p')}."
                )
        else:
            parts.append("No unknown visitors were detected.")

        if stats["masked_detections"]:
            parts.append(
                f"CRITICAL: {stats['masked_detections']} masked or face-covered individual(s) detected. "
                "Immediate review recommended."
            )

        if stats["asset_events"]:
            removed = sum(1 for e in events if e.event_type == EventType.ASSET_REMOVED)
            moved = sum(1 for e in events if e.event_type == EventType.ASSET_MOVED)
            returned = sum(1 for e in events if e.event_type == EventType.ASSET_RETURNED)
            asset_detail = []
            if removed:
                asset_detail.append(f"{removed} removal(s)")
            if moved:
                asset_detail.append(f"{moved} displacement(s)")
            if returned:
                asset_detail.append(f"{returned} return(s)")
            parts.append(f"Asset activity: {', '.join(asset_detail)}.")
        else:
            parts.append("No significant asset movements detected.")

        if incidents:
            parts.append(f"{len(incidents)} correlated incident(s) require attention:")
            for inc in incidents[:3]:
                parts.append(f"  • {inc.title} (Risk: {inc.risk_score:.0f})")
        else:
            parts.append("No correlated security incidents were identified.")

        door_events = [e for e in events if e.event_type in (EventType.DOOR_OPENED, EventType.DOOR_CLOSED)]
        if door_events:
            parts.append(f"{len(door_events)} door state change(s) logged.")

        parts.append(f"Average risk score: {stats['avg_risk_score']}/100.")
        parts.append(
            "Overall assessment: "
            + (
                "ELEVATED THREAT LEVEL — review critical events immediately."
                if stats["critical_events"] or stats["masked_detections"]
                else (
                    "MODERATE ACTIVITY — standard monitoring sufficient."
                    if stats["unknown_visitors"] or stats["asset_events"]
                    else "NORMAL — no significant anomalies detected."
                )
            )
        )

        return " ".join(parts)

    async def natural_language_query(
        self, db: AsyncSession, query: str, room_id: UUID | None = None
    ) -> tuple[str, list[Event]]:
        q_lower = query.lower()
        now = datetime.now(timezone.utc)

        if "yesterday" in q_lower:
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif "last week" in q_lower:
            start = now - timedelta(days=7)
            end = now
        elif "after 10" in q_lower or "after 10pm" in q_lower:
            start = (now - timedelta(days=1)).replace(hour=22, minute=0, second=0, microsecond=0)
            end = now
        else:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now

        events = await self._fetch_events(db, start, end, room_id)

        if "unknown" in q_lower:
            events = [e for e in events if e.event_type == EventType.UNKNOWN_PERSON]
            answer = f"Found {len(events)} unknown visitor event(s) in the specified period."
        elif "masked" in q_lower:
            events = [e for e in events if e.event_type == EventType.MASKED_PERSON]
            answer = f"Found {len(events)} masked person detection(s)."
        elif "laptop" in q_lower or "asset" in q_lower or "movement" in q_lower:
            events = [
                e
                for e in events
                if e.event_type
                in (EventType.ASSET_REMOVED, EventType.ASSET_MOVED, EventType.ASSET_RETURNED)
            ]
            answer = f"Found {len(events)} asset-related event(s)."
        elif "door" in q_lower:
            events = [e for e in events if e.event_type in (EventType.DOOR_OPENED, EventType.DOOR_CLOSED)]
            answer = f"Found {len(events)} door state change(s)."
        else:
            answer = f"Found {len(events)} total event(s) matching your query timeframe."

        return answer, events


ai_summary_service = AISummaryService()
