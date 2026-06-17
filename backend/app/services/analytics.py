"""Dashboard analytics and infographics data."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Camera, Event, Incident, SeverityLevel
from app.services.camera_health import is_camera_streaming
from app.schemas.responses import (
    AnalyticsResponse,
    DashboardStats,
    HeatmapCell,
    TimelinePoint,
)


class AnalyticsService:
    async def get_dashboard(self, db: AsyncSession) -> AnalyticsResponse:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        cameras = (await db.execute(select(Camera))).scalars().all()
        events_today = (
            await db.execute(select(Event).where(Event.created_at >= today_start))
        ).scalars().all()
        open_incidents = (
            await db.execute(select(Incident).where(Incident.status == "open"))
        ).scalars().all()

        from app.models.entities import EventType

        stats = DashboardStats(
            total_cameras=len(cameras),
            online_cameras=sum(1 for c in cameras if is_camera_streaming(c)),
            active_threats=len(open_incidents),
            events_today=len(events_today),
            unknown_visitors_today=sum(1 for e in events_today if e.event_type == EventType.UNKNOWN_PERSON),
            asset_alerts_today=sum(
                1
                for e in events_today
                if e.event_type.value.startswith("asset_")
            ),
            open_incidents=len(open_incidents),
            risk_score_avg=round(
                sum(i.risk_score for i in open_incidents) / max(len(open_incidents), 1), 1
            )
            if open_incidents
            else 0.0,
        )

        timeline = self._build_timeline(events_today)
        event_dist = {}
        severity_dist = {}
        for e in events_today:
            event_dist[e.event_type.value] = event_dist.get(e.event_type.value, 0) + 1
            severity_dist[e.severity.value] = severity_dist.get(e.severity.value, 0) + 1

        heatmap = self._build_heatmap(events_today)
        threat_events = [
            e for e in events_today
            if e.severity in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)
        ]
        top_threats = sorted(threat_events, key=lambda e: e.created_at, reverse=True)[:10]

        return AnalyticsResponse(
            stats=stats,
            timeline=timeline,
            event_distribution=event_dist,
            severity_distribution=severity_dist,
            heatmap=heatmap,
            top_threats=top_threats,
        )

    def _build_timeline(self, events: list[Event]) -> list[TimelinePoint]:
        hours: dict[int, dict] = {h: {"count": 0, "severity": {}} for h in range(24)}
        for e in events:
            h = e.created_at.hour
            hours[h]["count"] += 1
            sev = e.severity.value
            hours[h]["severity"][sev] = hours[h]["severity"].get(sev, 0) + 1

        return [
            TimelinePoint(hour=h, count=data["count"], severity_breakdown=data["severity"])
            for h, data in sorted(hours.items())
            if data["count"] > 0
        ]

    def _build_heatmap(self, events: list[Event]) -> list[HeatmapCell]:
        grid: dict[tuple[int, int], float] = {}
        for e in events:
            meta = e.event_metadata or {}
            pos = meta.get("position", {})
            if "x" in pos and "y" in pos:
                gx, gy = int(pos["x"] // 50), int(pos["y"] // 50)
                grid[(gx, gy)] = grid.get((gx, gy), 0) + e.risk_score / 100

        return [HeatmapCell(x=x, y=y, intensity=min(1.0, v)) for (x, y), v in grid.items()]


analytics_service = AnalyticsService()
