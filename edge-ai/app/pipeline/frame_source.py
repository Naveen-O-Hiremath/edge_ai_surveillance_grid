"""Fetch video frames from RTSP, browser buffer, or local webcam index."""

import base64
import logging

import cv2
import httpx
import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def decode_frame(frame_base64: str | None) -> np.ndarray | None:
    if not frame_base64:
        return None
    try:
        data = base64.b64decode(frame_base64)
        arr = np.frombuffer(data, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        logger.warning("Failed to decode frame: %s", e)
        return None


async def fetch_browser_frame(camera_id: str) -> np.ndarray | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.backend_url}/api/v1/internal/cameras/{camera_id}/frame")
            if resp.status_code != 200:
                return None
            arr = np.frombuffer(resp.content, dtype=np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        logger.debug("Browser frame fetch failed for %s: %s", camera_id, e)
        return None


def open_capture(stream_url: str, source_type: str = "rtsp"):
    if source_type == "webcam":
        return cv2.VideoCapture(0)
    if stream_url.startswith("browser://"):
        return None
    if stream_url.isdigit():
        return cv2.VideoCapture(int(stream_url))
    return cv2.VideoCapture(stream_url)


async def get_frame(
    camera_id: str,
    stream_url: str,
    source_type: str = "rtsp",
    frame_base64: str | None = None,
) -> np.ndarray | None:
    if frame_base64:
        frame = decode_frame(frame_base64)
        if frame is not None:
            return frame

    if source_type in ("webcam", "mobile") or stream_url.startswith("browser://"):
        return await fetch_browser_frame(camera_id)

    cap = open_capture(stream_url, source_type)
    if cap is None or not cap.isOpened():
        return None
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None
