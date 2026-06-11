"""Fallback when edge-ai is unreachable — never invent fake objects."""



from app.models.entities import Camera





async def run_demo_learning_scan(db, camera: Camera) -> dict:

    """Edge AI offline — cannot analyze frames. Return empty, never fake inventory."""

    return {

        "objects": [],

        "unknown_objects": [],

        "frame_obstructed": False,

        "detection_mode": "none",

        "message": "Edge AI service unavailable. Cannot analyze camera frame — check edge-ai container is running.",

    }


