"""Continuous surveillance — contextual situational events (no generic motion alerts)."""



import asyncio

import logging



import httpx



from app.config import get_settings

from app.pipeline.activity import detect_phone_usage

from app.pipeline.detector import ObjectDetector

from app.pipeline.event_cooldown import EventCooldown

from app.pipeline.event_narrator import (
    camera_covered,
    camera_disconnected,
    from_state_change,
    masked_person_detected,
    person_entered,
    person_left,
    person_visit,
    phone_in_use,
)
from app.pipeline.frame_analysis import is_frame_obstructed, is_frame_valid

from app.pipeline.face_recognition import FaceRecognizer

from app.pipeline.state_comparator import BaselineObject, StateComparator



logger = logging.getLogger(__name__)

settings = get_settings()





class SurveillanceEngine:

    def __init__(self):

        self.detector = ObjectDetector(confidence_threshold=settings.confidence_threshold / 100)

        self.comparator = StateComparator()

        self.face_recognizer = FaceRecognizer()

        self._active_sessions: dict[str, bool] = {}

        self._person_in_room: dict[str, int] = {}

        self._baseline: dict[str, list[BaselineObject]] = {}

        self._camera_configs: dict[str, dict[str, dict]] = {}

        self._cooldowns: dict[str, EventCooldown] = {}



    def set_baseline(self, room_id: str, objects: list[dict]):

        self._baseline[room_id] = [

            BaselineObject(

                name=o["name"],

                label=o.get("label", o["name"].lower()),

                bbox=(

                    o["location"]["bbox"]["x"],

                    o["location"]["bbox"]["y"],

                    o["location"]["bbox"]["width"],

                    o["location"]["bbox"]["height"],

                ),

                state=o.get("state", "present"),

                is_tracked=o.get("is_tracked", True),

            )

            for o in objects

        ]



    def load_known_persons(self, persons: list[dict]):

        self.face_recognizer.load_known_persons(persons)



    async def start(

        self,

        room_id: str,

        camera_ids: list[str],

        camera_configs: dict | None = None,

        known_persons: list[dict] | None = None,

    ):

        self._active_sessions[room_id] = True

        self._person_in_room[room_id] = 0

        self._cooldowns[room_id] = EventCooldown()

        if camera_configs:

            self._camera_configs[room_id] = camera_configs

        if known_persons:

            self.load_known_persons(known_persons)

        asyncio.create_task(self._surveillance_loop(room_id, camera_ids))

        logger.info("Surveillance started for room %s with %d cameras", room_id, len(camera_ids))



    async def stop(self, room_id: str):

        self._active_sessions[room_id] = False



    def _cooldown(self, room_id: str) -> EventCooldown:

        return self._cooldowns.setdefault(room_id, EventCooldown())



    async def _surveillance_loop(self, room_id: str, camera_ids: list[str]):

        from app.pipeline.frame_source import get_frame



        frame_count = 0

        primary_camera_id = camera_ids[0] if camera_ids else ""

        cam_config = self._camera_configs.get(room_id, {}).get(primary_camera_id, {})

        cd = self._cooldown(room_id)



        while self._active_sessions.get(room_id, False):

            frame_count += 1

            if frame_count % settings.frame_skip != 0:

                await asyncio.sleep(0.1)

                continue



            frame = await get_frame(
                primary_camera_id,
                cam_config.get("stream_url", ""),
                cam_config.get("source_type", "rtsp"),
            )

            events: list[dict] = []

            if not is_frame_valid(frame):
                key = f"{room_id}:camera_disconnected"
                if cd.allow(key, "camera_disconnected"):
                    title, desc = camera_disconnected()
                    events.append(self._make_event(
                        room_id, primary_camera_id, "camera_disconnected", title, desc, 90.0,
                    ))
                for event in events:
                    await self._send_event(event)
                await asyncio.sleep(0.35)
                continue

            # Blocked lens — log immediately (do not run YOLO on unusable frames)
            if is_frame_obstructed(frame):
                key = f"{room_id}:camera_covered"
                if cd.allow(key, "camera_covered"):
                    title, desc = camera_covered()
                    events.append(self._make_event(
                        room_id, primary_camera_id, "camera_covered", title, desc, 96.0,
                        metadata={"reason": "obstructed_frame"},
                    ))
                for event in events:
                    await self._send_event(event)
                await asyncio.sleep(0.35)
                continue

            detections = self.detector.detect(frame)



            persons = [d for d in detections if d.label == "person"]

            prev_count = self._person_in_room.get(room_id, 0)

            new_count = len(persons)



            if new_count > prev_count:

                entered = new_count - prev_count

                key = f"{room_id}:person_entered"

                if cd.allow(key, "person_entered"):

                    title, desc = person_entered(entered)

                    events.append(self._make_event(

                        room_id, primary_camera_id, "person_entered", title, desc, 85.0,

                    ))

            elif new_count < prev_count and prev_count > 0:

                if new_count == 0:

                    key = f"{room_id}:person_left"

                    if cd.allow(key, "person_exited"):

                        title, desc = person_left()

                        events.append(self._make_event(

                            room_id, primary_camera_id, "person_exited", title, desc, 88.0,

                        ))

                else:

                    key = f"{room_id}:person_partial_exit"

                    if cd.allow(key, "person_exited"):

                        title, desc = person_left()

                        events.append(self._make_event(

                            room_id, primary_camera_id, "person_exited", title, desc, 80.0,

                        ))



            self._person_in_room[room_id] = new_count



            if persons:

                face_results = self.face_recognizer.analyze_faces(frame, persons)

                for fr in face_results:

                    if fr.is_masked:
                        key = f"{room_id}:masked"
                        if cd.allow(key, "masked_person"):
                            title, desc = masked_person_detected()
                            events.append(self._make_event(
                                room_id, primary_camera_id, "masked_person", title, desc, fr.confidence,
                            ))

                    elif fr.is_known and fr.person_name:

                        key = f"{room_id}:known:{fr.person_id}"

                        if cd.allow(key, "known_person"):

                            title, desc = person_visit(fr.person_name, fr.person_role)

                            events.append(self._make_event(
                                room_id, primary_camera_id, "known_person", title, desc,
                                fr.confidence, person_id=fr.person_id,
                            ))

            if detect_phone_usage(persons, detections):

                key = f"{room_id}:phone_in_use"

                if cd.allow(key, "phone_in_use"):

                    title, desc = phone_in_use()

                    events.append(self._make_event(

                        room_id, primary_camera_id, "person_entered", title, desc, 82.0,

                        metadata={"activity": "phone_use"},

                    ))



            baseline = self._baseline.get(room_id, [])

            if baseline:

                changes = self.comparator.compare(baseline, detections)

                for change in changes:

                    key = f"{room_id}:{change.change_type}:{change.object_name}"

                    if not cd.allow(key, change.change_type):

                        continue

                    title, desc = from_state_change(change.change_type, change.object_name)

                    events.append(self._make_event(

                        room_id, primary_camera_id, change.change_type, title, desc, change.confidence,

                        metadata={"object_name": change.object_name},

                    ))



            for event in events:

                await self._send_event(event)



            await asyncio.sleep(0.4)



    def _make_event(

        self,

        room_id,

        camera_id,

        event_type,

        title,

        description,

        confidence,

        metadata=None,

        person_id=None,

    ) -> dict:

        return {

            "room_id": room_id,

            "camera_id": camera_id,

            "event_type": event_type,

            "title": title,

            "description": description,

            "confidence": confidence,

            "metadata": metadata,

            "person_id": person_id,

        }



    async def _send_event(self, event: dict):

        from uuid import UUID



        payload = dict(event)

        for key in ("person_id", "object_id"):

            val = payload.get(key)

            if val is not None:

                try:

                    UUID(str(val))

                except (ValueError, TypeError):

                    payload[key] = None

        try:

            async with httpx.AsyncClient(timeout=10.0) as client:

                resp = await client.post(f"{settings.backend_url}/api/v1/events/ingest", json=payload)

                resp.raise_for_status()

        except Exception as e:

            logger.warning("Failed to send event to backend: %s", e)





surveillance_engine = SurveillanceEngine()


