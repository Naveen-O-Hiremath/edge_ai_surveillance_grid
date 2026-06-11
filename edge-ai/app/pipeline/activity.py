"""Detect contextual activities from object + person detections."""



import math





def _center(bbox: tuple) -> tuple[float, float]:

    return bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2





def _distance(a: tuple, b: tuple) -> float:

    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)





def _boxes_overlap(a: tuple, b: tuple, margin: float = 40) -> bool:

    ax, ay, aw, ah = a

    bx, by, bw, bh = b

    return not (

        ax + aw + margin < bx

        or bx + bw + margin < ax

        or ay + ah + margin < by

        or by + bh + margin < ay

    )





def detect_phone_usage(persons: list, detections: list) -> bool:

    """True when a cell phone is near a person (likely in use)."""

    phones = [d for d in detections if d.label in ("cell phone", "remote")]

    if not phones or not persons:

        return False



    for phone in phones:

        phone_center = _center(phone.bbox)

        for person in persons:

            if _boxes_overlap(person.bbox, phone.bbox, margin=60):

                return True

            person_center = _center(person.bbox)

            dist = _distance(phone_center, person_center)

            person_size = max(person.bbox[2], person.bbox[3])

            if dist < person_size * 1.2:

                return True

    return False





def label_display_name(label: str, baseline_names: dict[str, str] | None = None) -> str:

    if baseline_names and label in baseline_names:

        return baseline_names[label]

    return label.replace("_", " ").title()


