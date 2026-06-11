"""Deduplicate and merge environment objects during learning scans."""



from __future__ import annotations



from app.models.entities import EnvironmentObject





def normalize_label(label: str) -> str:

    return label.strip().lower().replace(" ", "_")





def object_key(label: str, location: dict | None) -> tuple[str, str]:

    zone = ""

    if isinstance(location, dict):

        zone = str(location.get("zone") or "")

    return normalize_label(label), zone





def index_existing(objects: list[EnvironmentObject]) -> dict[tuple[str, str], EnvironmentObject]:

    indexed: dict[tuple[str, str], EnvironmentObject] = {}

    for obj in objects:

        indexed[object_key(obj.label, obj.location)] = obj

    return indexed





def merge_scan_object(

    existing_by_key: dict[tuple[str, str], EnvironmentObject],

    room_id,

    scanned: dict,

) -> tuple[EnvironmentObject, str, bool]:

    """

    Merge one scanned object into inventory.

    Returns (db_object, action, needs_admin_review).

    action: 'added' | 'updated' | 'skipped'

    """

    key = object_key(scanned["label"], scanned.get("location"))

    existing = existing_by_key.get(key)

    confidence = float(scanned.get("confidence", 0.0))

    admin_labeled = bool(scanned.get("admin_labeled", confidence >= 70.0))

    needs_review = not admin_labeled



    if existing:

        if existing.admin_labeled:

            return existing, "skipped", False



        changed = False

        if confidence > existing.confidence:

            existing.confidence = confidence

            existing.location = scanned.get("location", existing.location)

            existing.state = scanned.get("state", existing.state)

            changed = True



        if needs_review and not existing.admin_labeled:

            return existing, "updated" if changed else "skipped", True



        return existing, "updated" if changed else "skipped", False



    db_obj = EnvironmentObject(

        room_id=room_id,

        name=scanned["name"],

        label=scanned["label"],

        category=scanned.get("category", "general"),

        location=scanned["location"],

        state=scanned.get("state", "present"),

        confidence=confidence,

        admin_labeled=admin_labeled,

        relationships=scanned.get("relationships"),

        baseline_snapshot=scanned.get("snapshot_path"),

        is_tracked=admin_labeled,

    )

    existing_by_key[key] = db_obj

    return db_obj, "added", needs_review


