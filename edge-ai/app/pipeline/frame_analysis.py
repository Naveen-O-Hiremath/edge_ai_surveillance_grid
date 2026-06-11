"""Analyze frame quality — detect blocked/obstructed camera views."""



import logging



import cv2

import numpy as np



logger = logging.getLogger(__name__)





def is_frame_valid(frame) -> bool:

    return frame is not None and hasattr(frame, "shape") and frame.size > 0





def is_frame_obstructed(frame) -> bool:

    """

    Return True when the lens is covered (hand, cloth, cap) or the view is unusable.

    Uses brightness, texture (std dev), center-region uniformity, and edge density.

    """

    if not is_frame_valid(frame):

        return True



    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape

    mean = float(gray.mean())

    std = float(gray.std())



    if mean < 20:

        logger.debug("Frame obstructed: too dark (mean=%.1f)", mean)

        return True



    if std < 10:

        logger.debug("Frame obstructed: too uniform (std=%.1f)", std)

        return True



    cy, cx = h // 2, w // 2

    ch, cw = max(1, int(h * 0.65)), max(1, int(w * 0.65))

    y1, y2 = max(0, cy - ch // 2), min(h, cy + ch // 2)

    x1, x2 = max(0, cx - cw // 2), min(w, cx + cw // 2)

    center = gray[y1:y2, x1:x2]

    if center.size and center.std() < 14 and center.mean() < 90:

        logger.debug("Frame obstructed: uniform center region")

        return True



    edges = cv2.Canny(gray, 40, 120)

    edge_ratio = float(np.count_nonzero(edges)) / float(edges.size)

    if edge_ratio < 0.008:

        logger.debug("Frame obstructed: low edge density (%.4f)", edge_ratio)

        return True



    return False





def frame_stats(frame) -> dict:

    if not is_frame_valid(frame):

        return {"valid": False}

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    return {

        "valid": True,

        "width": int(frame.shape[1]),

        "height": int(frame.shape[0]),

        "brightness": round(float(gray.mean()), 1),

        "texture": round(float(gray.std()), 1),

        "obstructed": is_frame_obstructed(frame),

    }


