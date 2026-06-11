"""Prevent duplicate event spam during surveillance loops."""



import time





class EventCooldown:

    def __init__(self, default_seconds: float = 45.0):

        self._default = default_seconds

        self._last: dict[str, float] = {}

        self._intervals: dict[str, float] = {

            "person_entered": 30.0,

            "person_exited": 30.0,

            "phone_in_use": 60.0,

            "known_person": 120.0,

            "unknown_person": 90.0,

            "masked_person": 90.0,

            "asset_removed": 60.0,

            "asset_moved": 45.0,

            "new_asset": 60.0,

        }



    def allow(self, key: str, event_type: str | None = None) -> bool:

        now = time.monotonic()

        interval = self._intervals.get(event_type or "", self._default)

        last = self._last.get(key)

        if last is not None and (now - last) < interval:

            return False

        self._last[key] = now

        return True


