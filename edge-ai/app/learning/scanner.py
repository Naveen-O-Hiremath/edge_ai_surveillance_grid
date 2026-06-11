"""Phase 1 environment learning scanner — real frame analysis only."""



import logging



from app.pipeline.detector import ObjectDetector

from app.pipeline.frame_analysis import frame_stats, is_frame_obstructed, is_frame_valid

from app.config import get_settings



logger = logging.getLogger(__name__)

settings = get_settings()





class EnvironmentScanner:

    def __init__(self):

        self.detector = ObjectDetector(confidence_threshold=0.35)



    def scan(self, frame=None) -> dict:

        stats = frame_stats(frame)

        obstructed = stats.get("obstructed", True) if stats.get("valid") else True



        if not is_frame_valid(frame):

            return {

                "objects": [],

                "unknown_objects": [],

                "frame_obstructed": True,

                "detection_mode": self.detector.mode,

                "message": "No camera frame received.",

            }



        if obstructed:

            return {

                "objects": [],

                "unknown_objects": [],

                "frame_obstructed": True,

                "detection_mode": self.detector.mode,

                "message": "Camera appears blocked or covered. Remove your hand and point at the room.",

            }



        detections = self.detector.detect(frame)

        objects = []

        unknown_objects = []



        seen_keys: set[tuple[str, str]] = set()

        h = frame.shape[0]

        for det in detections:

            zone = self._infer_zone(det.bbox, h)

            key = (det.label.strip().lower(), zone)

            if key in seen_keys:

                continue

            seen_keys.add(key)



            obj = {

                "name": det.label.replace(" ", "_").title(),

                "label": det.label,

                "category": self._categorize(det.label),

                "location": {

                    "bbox": {

                        "x": round(det.bbox[0], 1),

                        "y": round(det.bbox[1], 1),

                        "width": round(det.bbox[2], 1),

                        "height": round(det.bbox[3], 1),

                    },

                    "zone": zone,

                },

                "state": self._infer_state(det.label),

                "confidence": det.confidence,

                "admin_labeled": det.confidence >= settings.unknown_threshold,

                "relationships": None,

            }

            objects.append(obj)



            if det.confidence < settings.unknown_threshold:

                unknown_objects.append({

                    "object_id": "pending",

                    "label": det.label,

                    "confidence": det.confidence,

                    "location": obj["location"],

                    "snapshot_path": None,

                    "message": f"What is this object? (detected as '{det.label}' with {det.confidence:.1f}% confidence)",

                })



        msg = f"Detected {len(objects)} object(s) in current frame." if objects else (

            "No objects detected in frame. Point camera at your desk/room with a clear view."

        )



        return {

            "objects": objects,

            "unknown_objects": unknown_objects,

            "frame_obstructed": False,

            "detection_mode": self.detector.mode,

            "frame_stats": stats,

            "message": msg,

        }



    def _categorize(self, label: str) -> str:

        electronics = {"laptop", "mouse", "keyboard", "cell phone", "tv", "monitor", "remote"}

        furniture = {"chair", "couch", "bed", "dining table"}

        if label in electronics:

            return "electronics"

        if label in furniture:

            return "furniture"

        if label == "person":

            return "person"

        return "general"



    def _infer_zone(self, bbox, frame_height: int) -> str:

        y = bbox[1]

        threshold_wall = frame_height * 0.25

        threshold_desk = frame_height * 0.55

        if y < threshold_wall:

            return "wall"

        if y < threshold_desk:

            return "desk"

        return "floor"



    def _infer_state(self, label: str) -> str:

        if label in ("monitor", "laptop", "tv"):

            return "on"

        return "present"


