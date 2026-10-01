"""Sample gigs for trying out the dashboard without a Bandsintown key.

The sample file uses the same format as the real Bandsintown API. Dates are
shifted so the gigs always sit around today's date, however old the file is.
"""
import copy
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from . import Event
from .bandsintown import parse_event


def load_sample_events(path: Path, today: date) -> list[Event]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    shift = today - date.fromisoformat(data["anchor_date"])

    events = []
    for raw in data["events"]:
        raw = copy.deepcopy(raw)
        for key in ("datetime", "starts_at"):
            if raw.get(key):
                moved = datetime.fromisoformat(raw[key][:19]) + timedelta(days=shift.days)
                raw[key] = moved.isoformat(timespec="seconds")
        events.append(parse_event(raw))
    return events
