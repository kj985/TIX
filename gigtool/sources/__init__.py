"""Places gigs come from.

Each source turns its own data into a list of Event objects, which the
importer then saves. To add another source later (e.g. a ticketing site),
write a new module here that returns Event objects.
"""
from dataclasses import dataclass, field


@dataclass
class Event:
    source_event_id: str
    starts_at: str  # venue local time, 'YYYY-MM-DDTHH:MM:SS'
    title: str = ""
    venue_name: str = ""
    city: str = ""
    region: str = ""
    country: str = ""
    ticket_url: str | None = None
    event_url: str | None = None
    lineup: list[str] = field(default_factory=list)
    description: str = ""
    raw: dict = field(default_factory=dict)
