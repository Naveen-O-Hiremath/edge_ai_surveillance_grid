"""Deterministic state comparison — detect misplaced/removed assets without AI."""

import math
from dataclasses import dataclass


@dataclass
class BaselineObject:
    name: str
    label: str
    bbox: tuple[float, float, float, float]
    state: str
    is_tracked: bool = True


@dataclass
class StateChange:
    change_type: str
    object_name: str
    details: str
    confidence: float


class StateComparator:
    IOU_THRESHOLD = 0.3
    POSITION_TOLERANCE = 80.0

    def compare(
        self,
        baseline: list[BaselineObject],
        current_detections: list,
    ) -> list[StateChange]:
        changes = []
        matched_baseline = set()

        for det in current_detections:
            best_match = None
            best_iou = 0
            for obj in baseline:
                if obj.label != det.label and obj.name.lower() not in det.label:
                    continue
                iou = self._iou(obj.bbox, det.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_match = obj

            if best_match and best_iou >= self.IOU_THRESHOLD:
                matched_baseline.add(best_match.name)
                displacement = self._center_distance(best_match.bbox, det.bbox)
                if displacement > self.POSITION_TOLERANCE and best_match.is_tracked:
                    changes.append(
                        StateChange(
                            change_type="asset_moved",
                            object_name=best_match.name,
                            details=f"{best_match.name} displaced by {displacement:.0f}px",
                            confidence=85.0 + min(10, displacement / 20),
                        )
                    )
            elif det.confidence > 80:
                changes.append(
                    StateChange(
                        change_type="new_asset",
                        object_name=det.label,
                        details=f"New object detected: {det.label}",
                        confidence=det.confidence,
                    )
                )

        for obj in baseline:
            if obj.is_tracked and obj.name not in matched_baseline:
                changes.append(
                    StateChange(
                        change_type="asset_removed",
                        object_name=obj.name,
                        details=f"{obj.name} no longer detected at baseline location",
                        confidence=88.0,
                    )
                )

        return changes

    def compare_screen_state(self, frame, monitor_roi: tuple, prev_brightness: float | None) -> str | None:
        """Detect monitor on/off via brightness — no AI."""
        if frame is None:
            return None
        x, y, w, h = monitor_roi
        roi = frame[y : y + h, x : x + w]
        import cv2
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        brightness = float(gray.mean())
        if prev_brightness is not None:
            if prev_brightness > 80 and brightness < 30:
                return "off"
            if prev_brightness < 30 and brightness > 80:
                return "on"
        return None

    @staticmethod
    def _iou(a: tuple, b: tuple) -> float:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        x1 = max(ax, bx)
        y1 = max(ay, by)
        x2 = min(ax + aw, bx + bw)
        y2 = min(ay + ah, by + bh)
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        union = aw * ah + bw * bh - inter
        return inter / union if union > 0 else 0

    @staticmethod
    def _center_distance(a: tuple, b: tuple) -> float:
        acx, acy = a[0] + a[2] / 2, a[1] + a[3] / 2
        bcx, bcy = b[0] + b[2] / 2, b[1] + b[3] / 2
        return math.sqrt((acx - bcx) ** 2 + (acy - bcy) ** 2)
