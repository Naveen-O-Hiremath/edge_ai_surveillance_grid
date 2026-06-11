"""Threat assessment engine — deterministic rule-based scoring."""

from app.models.entities import EventType, SeverityLevel
from app.schemas.common import ThreatAssessment

SEVERITY_ORDER = {
    SeverityLevel.INFO: 0,
    SeverityLevel.LOW: 1,
    SeverityLevel.MEDIUM: 2,
    SeverityLevel.HIGH: 3,
    SeverityLevel.CRITICAL: 4,
}

EVENT_THREAT_PROFILE: dict[EventType, tuple[SeverityLevel, float, float]] = {
    EventType.PERSON_ENTERED: (SeverityLevel.INFO, 85.0, 10.0),
    EventType.PERSON_EXITED: (SeverityLevel.INFO, 85.0, 5.0),
    EventType.KNOWN_PERSON: (SeverityLevel.INFO, 90.0, 5.0),
    EventType.PERSON_LOITERING: (SeverityLevel.MEDIUM, 80.0, 45.0),
    EventType.UNKNOWN_PERSON: (SeverityLevel.HIGH, 85.0, 70.0),
    EventType.MASKED_PERSON: (SeverityLevel.CRITICAL, 92.0, 95.0),
    EventType.FACE_COVERED: (SeverityLevel.HIGH, 88.0, 80.0),
    EventType.MULTIPLE_PERSONS: (SeverityLevel.MEDIUM, 75.0, 35.0),
    EventType.TAILGATING: (SeverityLevel.HIGH, 82.0, 75.0),
    EventType.ASSET_REMOVED: (SeverityLevel.HIGH, 88.0, 78.0),
    EventType.ASSET_MOVED: (SeverityLevel.MEDIUM, 80.0, 40.0),
    EventType.ASSET_RETURNED: (SeverityLevel.LOW, 85.0, 15.0),
    EventType.NEW_ASSET: (SeverityLevel.LOW, 70.0, 20.0),
    EventType.DOOR_OPENED: (SeverityLevel.LOW, 90.0, 15.0),
    EventType.DOOR_CLOSED: (SeverityLevel.INFO, 95.0, 5.0),
    EventType.WINDOW_OPENED: (SeverityLevel.MEDIUM, 85.0, 35.0),
    EventType.LIGHTS_ON: (SeverityLevel.INFO, 90.0, 5.0),
    EventType.LIGHTS_OFF: (SeverityLevel.LOW, 85.0, 15.0),
    EventType.MONITOR_ON: (SeverityLevel.INFO, 92.0, 5.0),
    EventType.MONITOR_OFF: (SeverityLevel.LOW, 88.0, 20.0),
    EventType.CAMERA_COVERED: (SeverityLevel.CRITICAL, 95.0, 98.0),
    EventType.CAMERA_TAMPERED: (SeverityLevel.CRITICAL, 93.0, 96.0),
    EventType.CAMERA_DISCONNECTED: (SeverityLevel.CRITICAL, 99.0, 99.0),
    EventType.MOTION_DETECTED: (SeverityLevel.LOW, 70.0, 15.0),
    EventType.SOUND_ANOMALY: (SeverityLevel.MEDIUM, 65.0, 30.0),
}


class ThreatEngine:
    def assess(
        self,
        event_type: EventType,
        confidence: float,
        context: dict | None = None,
    ) -> ThreatAssessment:
        base_severity, base_confidence, base_risk = EVENT_THREAT_PROFILE.get(
            event_type,
            (SeverityLevel.INFO, 50.0, 10.0),
        )

        adjusted_confidence = min(100.0, (confidence + base_confidence) / 2)
        risk_score = base_risk

        if context:
            if context.get("after_hours"):
                risk_score = min(100.0, risk_score * 1.3)
            if context.get("repeat_unknown"):
                risk_score = min(100.0, risk_score * 1.2)
            if context.get("authorized_zone"):
                risk_score = max(0.0, risk_score * 0.7)

        severity = self._escalate_severity(base_severity, risk_score)

        return ThreatAssessment(
            severity=severity,
            confidence=round(adjusted_confidence, 1),
            risk_score=round(risk_score, 1),
        )

    def _escalate_severity(self, base: SeverityLevel, risk_score: float) -> SeverityLevel:
        if risk_score >= 90:
            return SeverityLevel.CRITICAL
        if risk_score >= 70:
            return max(base, SeverityLevel.HIGH, key=lambda s: SEVERITY_ORDER[s])
        if risk_score >= 45:
            return max(base, SeverityLevel.MEDIUM, key=lambda s: SEVERITY_ORDER[s])
        return base

    def meets_threshold(self, severity: SeverityLevel, min_severity: SeverityLevel) -> bool:
        return SEVERITY_ORDER[severity] >= SEVERITY_ORDER[min_severity]


threat_engine = ThreatEngine()
