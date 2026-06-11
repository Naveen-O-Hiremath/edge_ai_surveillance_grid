"""

Object detection layer — YOLO on real frames only.

Never returns hardcoded/fake objects.

"""



import logging

import os

from dataclasses import dataclass



from app.config import get_settings

from app.pipeline.frame_analysis import is_frame_obstructed, is_frame_valid



logger = logging.getLogger(__name__)

settings = get_settings()



# COCO classes useful for office/desk surveillance

RELEVANT_LABELS = {

    "person", "laptop", "mouse", "keyboard", "cell phone", "tv", "chair",

    "couch", "bed", "dining table", "bottle", "cup", "book", "clock",

    "potted plant", "backpack", "handbag", "suitcase", "remote", "microwave",

    "oven", "toaster", "sink", "refrigerator", "vase", "scissors", "teddy bear",

    "hair drier", "toothbrush",

}





@dataclass

class Detection:

    label: str

    confidence: float

    bbox: tuple[float, float, float, float]

    class_id: int = -1





class ObjectDetector:

    """Detects objects in the actual camera frame using YOLO."""



    def __init__(self, confidence_threshold: float = 0.35):

        self.confidence_threshold = confidence_threshold

        self._model = None

        self._mode = "none"

        self._try_load_model()



    @property

    def mode(self) -> str:

        return self._mode



    def _try_load_model(self):

        try:

            from ultralytics import YOLO



            model_path = os.path.join(settings.model_cache, "yolov8n.pt")

            if os.path.isfile(model_path):

                self._model = YOLO(model_path)

            else:

                self._model = YOLO("yolov8n.pt")

            self._mode = "yolo"

            logger.info("YOLO model loaded (%s)", model_path if os.path.isfile(model_path) else "auto-download")

        except Exception as e:

            self._model = None

            self._mode = "none"

            logger.error("YOLO unavailable — real detection disabled: %s", e)



    def detect(self, frame) -> list[Detection]:

        if not is_frame_valid(frame):

            logger.warning("No valid frame — returning empty detections")

            return []



        if is_frame_obstructed(frame):

            logger.info("Camera obstructed/covered — returning empty detections")

            return []



        if self._model is not None:

            return self._detect_yolo(frame)



        logger.warning("No detection model — cannot analyze frame")

        return []



    def _detect_yolo(self, frame) -> list[Detection]:

        results = self._model(frame, verbose=False)

        detections: list[Detection] = []

        for r in results:

            for box in r.boxes:

                conf = float(box.conf[0])

                if conf < self.confidence_threshold:

                    continue

                cls_id = int(box.cls[0])

                label = r.names.get(cls_id, "unknown")

                if label not in RELEVANT_LABELS:

                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detections.append(

                    Detection(label, round(conf * 100, 1), (x1, y1, x2 - x1, y2 - y1), cls_id)

                )

        logger.info("YOLO detected %d object(s) in frame", len(detections))

        return detections


