import json
import logging

logger = logging.getLogger(__name__)


class MQTTPublisher:
    def __init__(self):
        self._connected = False

    async def publish(self, topic: str, payload: dict) -> None:
        logger.info("MQTT publish [%s]: %s", topic, json.dumps(payload, default=str)[:200])


mqtt_publisher = MQTTPublisher()
