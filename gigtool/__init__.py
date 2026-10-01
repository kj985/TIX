"""Gig promotion tool for Sarah McLeod.

Stage 1: import gigs from Bandsintown, tag them by project, and track
ad budget / notes / tickets sold in a local dashboard.
"""
from pathlib import Path

# The folder that contains config.toml, data/ and sample_data/.
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "gigs.db"
SAMPLE_EVENTS_PATH = BASE_DIR / "sample_data" / "bandsintown_events.json"
