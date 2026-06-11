"""Human-readable situational event messages."""



from datetime import datetime, timezone





def _now_label() -> str:

    return datetime.now(timezone.utc).strftime("%I:%M %p").lstrip("0")





def _display_name(label_or_name: str) -> str:

    return label_or_name.replace("_", " ").strip().title()





def person_entered(count: int = 1) -> tuple[str, str]:

    if count == 1:

        title = "Person entered the area"

        desc = f"Someone entered the monitored space at {_now_label()}"

    else:

        title = f"{count} people entered the area"

        desc = f"{count} individuals entered at {_now_label()}"

    return title, desc





def person_left() -> tuple[str, str]:

    t = _now_label()

    title = f"Person left at {t}"

    desc = f"The area is now empty — last person left at {t}"

    return title, desc





def person_visit(name: str, role: str | None = None) -> tuple[str, str]:

    role_part = f" ({role})" if role else ""

    title = f"{name} visited the place"

    desc = f"Registered person{role_part} recognized in the monitored area at {_now_label()}"

    return title, desc





def unknown_person_detected() -> tuple[str, str]:

    title = "Unknown person detected"

    desc = f"An unrecognized individual is in the monitored area at {_now_label()}"

    return title, desc





def masked_person_detected() -> tuple[str, str]:

    title = "Face-covered individual detected"

    desc = f"Person with obscured face detected at {_now_label()}"

    return title, desc





def phone_in_use() -> tuple[str, str]:

    title = "Using phone detected"

    desc = f"Someone appears to be using a cell phone at {_now_label()}"

    return title, desc





def asset_detected(name: str) -> tuple[str, str]:

    display = _display_name(name)

    title = f"{display} detected"

    desc = f"{display} is visible in the camera frame at {_now_label()}"

    return title, desc





def asset_removed(name: str) -> tuple[str, str]:

    display = _display_name(name)

    title = f"{display} removed"

    desc = f"{display} is no longer visible at its usual location ({_now_label()})"

    return title, desc





def asset_moved(name: str) -> tuple[str, str]:

    display = _display_name(name)

    title = f"{display} moved"

    desc = f"{display} was repositioned from its baseline location at {_now_label()}"

    return title, desc





def from_state_change(change_type: str, object_name: str) -> tuple[str, str]:

    name = _display_name(object_name)

    if change_type == "asset_removed":

        return asset_removed(name)

    if change_type == "asset_moved":

        return asset_moved(name)

    if change_type == "new_asset":

        return asset_detected(name)

    return (f"{name} — activity detected", f"Change detected for {name} at {_now_label()}")


