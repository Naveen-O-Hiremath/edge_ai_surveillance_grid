"""Deterministic motion detection — no AI required."""

import cv2
import numpy as np


class MotionDetector:
    def __init__(self, sensitivity: float = 0.02):
        self.sensitivity = sensitivity
        self._prev_gray = None
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

    def detect(self, frame) -> tuple[bool, float, dict | None]:
        if frame is None:
            return False, 0.0, None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self._prev_gray is None:
            self._prev_gray = gray
            return False, 0.0, None

        diff = cv2.absdiff(self._prev_gray, gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self._prev_gray = gray

        if not contours:
            return False, 0.0, None

        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        frame_area = frame.shape[0] * frame.shape[1]
        ratio = area / frame_area

        if ratio < self.sensitivity:
            return False, ratio, None

        x, y, w, h = cv2.boundingRect(largest)
        return True, ratio, {"x": float(x), "y": float(y), "width": float(w), "height": float(h)}

    def detect_door_state(self, frame, door_roi: tuple[int, int, int, int]) -> str | None:
        """Compare door region brightness/edges to detect open/close."""
        if frame is None:
            return None
        x, y, w, h = door_roi
        roi = frame[y : y + h, x : x + w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (w * h)
        return "open" if edge_density > 0.15 else "closed"
