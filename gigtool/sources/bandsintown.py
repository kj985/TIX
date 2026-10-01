"""Fetches upcoming events from the Bandsintown API.

About the API and app_id: https://help.artists.bandsintown.com/en/articles/7053475-api-and-app-id
"""
from urllib.parse import quote

import requests

from . import Event

API_BASE = "https://rest.bandsintown.com"


class BandsintownError(Exception):
    pass


def encode_artist_name(name: str) -> str:
    # Bandsintown needs a few characters double-encoded in the artist name.
    special = {"/": "%252F", "?": "%253F", "*": "%252A", '"': "%27C"}
    return "".join(special.get(ch, quote(ch, safe="")) for ch in name)


def fetch_upcoming(artist_name: str, app_id: str, timeout: int = 20) -> list[dict]:
    url = f"{API_BASE}/artists/{encode_artist_name(artist_name)}/events"
    try:
        resp = requests.get(url, params={"app_id": app_id, "date": "upcoming"}, timeout=timeout)
    except requests.RequestException as e:
        raise BandsintownError(
            f"Couldn't reach Bandsintown. Check your internet connection. ({type(e).__name__})"
        ) from e

    if resp.status_code in (401, 403):
        raise BandsintownError(
            "Bandsintown rejected the app_id. Check it in config.toml matches the API key "
            "in Bandsintown for Artists."
        )
    if resp.status_code == 404:
        raise BandsintownError(f'Bandsintown couldn\'t find an artist called "{artist_name}".')
    if not resp.ok:
        raise BandsintownError(f"Bandsintown returned an error ({resp.status_code}). Try again later.")

    try:
        data = resp.json()
    except ValueError as e:
        raise BandsintownError("Bandsintown sent back something that wasn't valid data.") from e

    if isinstance(data, dict):
        message = data.get("errorMessage") or data.get("message") or str(data)
        raise BandsintownError(f"Bandsintown said: {message}")
    if not isinstance(data, list):
        raise BandsintownError("Bandsintown sent back data in an unexpected format.")
    return data


def _ticket_url(offers: list[dict]) -> str | None:
    for offer in offers:
        if str(offer.get("type", "")).lower() == "tickets" and offer.get("url"):
            return offer["url"]
    for offer in offers:
        if offer.get("url"):
            return offer["url"]
    return None


def parse_event(raw: dict) -> Event:
    venue = raw.get("venue") or {}
    starts_at = str(raw.get("starts_at") or raw.get("datetime") or "")[:19]
    if not starts_at:
        raise BandsintownError(f"Event {raw.get('id')} has no date.")
    return Event(
        source_event_id=str(raw["id"]),
        starts_at=starts_at,
        title=raw.get("title") or "",
        venue_name=venue.get("name") or venue.get("location") or "",
        city=venue.get("city") or "",
        region=venue.get("region") or "",
        country=venue.get("country") or "",
        ticket_url=_ticket_url(raw.get("offers") or []),
        event_url=raw.get("url"),
        lineup=[str(name) for name in raw.get("lineup") or []],
        description=raw.get("description") or "",
        raw=raw,
    )
