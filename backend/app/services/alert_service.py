"""Alert routing — push, SMS, email, desktop, audible."""

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AlertRule, Event, SeverityLevel
from app.services.threat_engine import SEVERITY_ORDER, threat_engine

logger = logging.getLogger(__name__)


class AlertService:
    async def dispatch_for_event(self, db: AsyncSession, event: Event) -> list[dict]:
        result = await db.execute(select(AlertRule).where(AlertRule.is_active.is_(True)))
        rules = result.scalars().all()

        dispatched: list[dict] = []
        for rule in rules:
            if rule.event_type != event.event_type:
                continue
            if not threat_engine.meets_threshold(event.severity, rule.min_severity):
                continue
            if rule.room_ids and str(event.room_id) not in [str(r) for r in rule.room_ids]:
                continue

            payload = {
                "rule_id": str(rule.id),
                "rule_name": rule.name,
                "event_id": str(event.id),
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "title": event.title,
                "description": event.description,
                "room_id": str(event.room_id),
                "channels": rule.channels,
                "sound_enabled": rule.sound_enabled,
                "risk_score": event.risk_score,
            }
            await self._send_to_channels(payload)
            dispatched.append(payload)

        return dispatched

    async def _send_to_channels(self, payload: dict) -> None:
        for channel in payload.get("channels", []):
            match channel:
                case "push":
                    await self._send_push(payload)
                case "sms":
                    await self._send_sms(payload)
                case "whatsapp":
                    await self._send_whatsapp(payload)
                case "email":
                    await self._send_email(payload)
                case "desktop":
                    await self._send_desktop(payload)
                case _:
                    logger.warning("Unknown alert channel: %s", channel)

        if payload.get("sound_enabled"):
            await self._trigger_audible_alarm(payload)

    async def _send_push(self, payload: dict) -> None:
        logger.info("PUSH ALERT: %s", json.dumps(payload, default=str))
        # MQTT topic for mobile app
        try:
            from app.services.mqtt_client import mqtt_publisher

            await mqtt_publisher.publish("sentinel/alerts/push", payload)
        except Exception as e:
            logger.debug("MQTT push unavailable: %s", e)

    async def _send_sms(self, payload: dict) -> None:
        logger.info("SMS ALERT: %s — %s", payload["severity"], payload["title"])

    async def _send_whatsapp(self, payload: dict) -> None:
        logger.info("WHATSAPP ALERT: %s — %s", payload["severity"], payload["title"])

    async def _send_email(self, payload: dict) -> None:
        logger.info("EMAIL ALERT: %s — %s", payload["severity"], payload["title"])

    async def _send_desktop(self, payload: dict) -> None:
        try:
            from app.websocket import manager

            await manager.broadcast({"type": "alert", "data": payload})
        except Exception as e:
            logger.debug("WebSocket broadcast unavailable: %s", e)

    async def _trigger_audible_alarm(self, payload: dict) -> None:
        if SEVERITY_ORDER.get(SeverityLevel(payload["severity"]), 0) >= SEVERITY_ORDER[SeverityLevel.HIGH]:
            try:
                from app.websocket import manager

                await manager.broadcast({"type": "alarm", "data": payload})
            except Exception:
                pass


alert_service = AlertService()
