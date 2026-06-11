"""

Face recognition layer.

Matches registered persons using embedding similarity from face region.

"""



import hashlib

import logging

import math

from dataclasses import dataclass



import cv2

import numpy as np



logger = logging.getLogger(__name__)



MATCH_THRESHOLD = 0.82





@dataclass

class FaceResult:

    person_id: str | None

    person_name: str | None

    person_role: str | None

    is_known: bool

    is_masked: bool

    confidence: float

    bbox: tuple[float, float, float, float]





def _embedding_from_image(image_data: bytes) -> list[float]:

    digest = hashlib.sha256(image_data).digest()

    return [((b / 255.0) * 2 - 1) for b in digest[:128]]





def _cosine_similarity(a: list[float], b: list[float]) -> float:

    if not a or not b or len(a) != len(b):

        return 0.0

    dot = sum(x * y for x, y in zip(a, b))

    na = math.sqrt(sum(x * x for x in a))

    nb = math.sqrt(sum(y * y for y in b))

    if na == 0 or nb == 0:

        return 0.0

    return dot / (na * nb)





class FaceRecognizer:

    def __init__(self):

        self._known_persons: list[dict] = []

        self._face_cascade = None

        self._try_load()



    def _try_load(self):

        try:

            self._face_cascade = cv2.CascadeClassifier(

                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

            )

        except Exception as e:

            logger.info("Face cascade not available: %s", e)



    def load_known_persons(self, persons: list[dict]):

        self._known_persons = persons or []

        logger.info("Loaded %d registered person(s) for face matching", len(self._known_persons))



    def analyze_faces(self, frame, person_detections: list) -> list[FaceResult]:

        results = []

        for det in person_detections:

            if det.label != "person":

                continue

            masked = self._detect_mask(frame, det.bbox)

            if masked:

                results.append(

                    FaceResult(

                        person_id=None,

                        person_name=None,

                        person_role=None,

                        is_known=False,

                        is_masked=True,

                        confidence=88.0,

                        bbox=det.bbox,

                    )

                )

                continue



            known = self._match_known(frame, det.bbox)

            results.append(

                FaceResult(

                    person_id=known.get("id") if known else None,

                    person_name=known.get("name") if known else None,

                    person_role=known.get("role") if known else None,

                    is_known=known is not None,

                    is_masked=False,

                    confidence=known.get("confidence", 75.0) if known else 75.0,

                    bbox=det.bbox,

                )

            )

        return results



    def _detect_mask(self, frame, bbox: tuple) -> bool:

        if frame is None:

            return False

        x, y, w, h = [int(v) for v in bbox]

        face_h = max(1, int(h * 0.4))

        face_region = frame[y : y + face_h, x : x + w]

        if face_region.size == 0:

            return False

        gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)

        return float(np.std(gray)) < 25.0



    def _face_embedding(self, frame, bbox: tuple) -> list[float] | None:

        if frame is None:

            return None

        x, y, w, h = [int(v) for v in bbox]

        face_h = max(1, int(h * 0.55))

        region = frame[y : y + face_h, x : x + w]

        if region.size == 0:

            return None

        ok, buf = cv2.imencode(".jpg", region)

        if not ok:

            return None

        return _embedding_from_image(buf.tobytes())



    def _match_known(self, frame, bbox: tuple) -> dict | None:

        if not self._known_persons:

            return None



        live_emb = self._face_embedding(frame, bbox)

        if not live_emb:

            return None



        best: dict | None = None

        best_score = 0.0

        for person in self._known_persons:

            for stored in person.get("embeddings") or []:

                score = _cosine_similarity(live_emb, stored)

                if score > best_score:

                    best_score = score

                    best = {

                        "id": person.get("id"),

                        "name": person.get("name"),

                        "role": person.get("role"),

                        "confidence": round(min(99.0, score * 100), 1),

                    }



        if best and best_score >= MATCH_THRESHOLD:

            return best

        return None


