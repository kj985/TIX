"""Saves imported events into the database without losing your edits.

Rules:
- A gig is matched to its Bandsintown event ID, so re-importing updates it
  rather than creating a duplicate.
- Only the Bandsintown fields (date, venue, ticket link, etc.) are refreshed.
  Ad budget, notes, tickets sold and ticket-link override are never touched.
- The project tag is re-detected only if you haven't set it by hand.
- Gigs are never deleted. An upcoming gig that vanishes from Bandsintown
  (often a cancellation) is flagged instead.
"""
import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone

from .config import Config
from .projects import detect_project
from .sources import Event


@dataclass
class ImportResult:
    added: int = 0
    updated: int = 0
    flagged_missing: int = 0

    def summary(self) -> str:
        parts = [f"{self.added} new", f"{self.updated} updated"]
        if self.flagged_missing:
            parts.append(f"{self.flagged_missing} no longer on Bandsintown (check if cancelled)")
        return ", ".join(parts)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def import_events(
    conn: sqlite3.Connection, source: str, events: list[Event], config: Config, today: date
) -> ImportResult:
    result = ImportResult()
    now = _now()

    for ev in events:
        detection = detect_project(
            ev.title, ev.lineup, ev.description, config.projects, config.fallback_project
        )
        imported = {
            "title": ev.title,
            "starts_at": ev.starts_at,
            "venue_name": ev.venue_name,
            "city": ev.city,
            "region": ev.region,
            "country": ev.country,
            "ticket_url": ev.ticket_url,
            "event_url": ev.event_url,
            "lineup": json.dumps(ev.lineup),
            "description": ev.description,
            "raw_json": json.dumps(ev.raw),
        }
        existing = conn.execute(
            "SELECT id, project_source FROM gigs WHERE source = ? AND source_event_id = ?",
            (source, ev.source_event_id),
        ).fetchone()

        if existing is None:
            cols = list(imported) + [
                "source", "source_event_id", "first_imported_at", "last_imported_at",
                "project", "project_source", "project_reason",
            ]
            values = list(imported.values()) + [
                source, ev.source_event_id, now, now,
                detection.project, "auto", detection.reason,
            ]
            placeholders = ", ".join("?" for _ in cols)
            conn.execute(f"INSERT INTO gigs ({', '.join(cols)}) VALUES ({placeholders})", values)
            result.added += 1
        else:
            updates = dict(imported, last_imported_at=now, missing_from_source=0)
            if existing["project_source"] == "auto":
                updates["project"] = detection.project
                updates["project_reason"] = detection.reason
            assignments = ", ".join(f"{col} = ?" for col in updates)
            conn.execute(
                f"UPDATE gigs SET {assignments} WHERE id = ?",
                list(updates.values()) + [existing["id"]],
            )
            result.updated += 1

    # Flag upcoming gigs from this source that weren't in this import.
    seen = [ev.source_event_id for ev in events]
    placeholders = ", ".join("?" for _ in seen) or "''"
    cur = conn.execute(
        f"""UPDATE gigs SET missing_from_source = 1
            WHERE source = ? AND starts_at >= ? AND missing_from_source = 0
              AND source_event_id NOT IN ({placeholders})""",
        [source, today.isoformat()] + seen,
    )
    result.flagged_missing = cur.rowcount

    conn.commit()
    return result


def run_bandsintown_import(conn: sqlite3.Connection, config: Config) -> ImportResult:
    from .sources.bandsintown import BandsintownError, fetch_upcoming, parse_event

    if not config.has_api_credentials:
        raise BandsintownError(
            "No Bandsintown app_id yet. Add it to config.toml (see README), "
            "or use the sample gigs for now."
        )
    raw_events = fetch_upcoming(config.artist_name, config.app_id)
    events = [parse_event(raw) for raw in raw_events]
    return import_events(conn, "bandsintown", events, config, config.today())


def run_sample_import(conn: sqlite3.Connection, config: Config, path) -> ImportResult:
    from .sources.sample import load_sample_events

    today = config.today()
    return import_events(conn, "sample", load_sample_events(path, today), config, today)
