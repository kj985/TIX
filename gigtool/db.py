"""Local SQLite database (a single file: data/gigs.db).

The schema is built from a numbered list of migrations. To add tables later
(e.g. Meta ad campaigns, click tracking), append a new entry to MIGRATIONS;
existing databases are upgraded automatically and no data is lost.
"""
import sqlite3
from pathlib import Path

MIGRATIONS = [
    # 1: gigs
    """
    CREATE TABLE gigs (
        id                  INTEGER PRIMARY KEY,
        source              TEXT NOT NULL,      -- 'bandsintown' or 'sample'
        source_event_id     TEXT NOT NULL,

        -- Copied from Bandsintown; refreshed on every import.
        title               TEXT,
        starts_at           TEXT NOT NULL,      -- venue local time, 'YYYY-MM-DDTHH:MM:SS'
        venue_name          TEXT,
        city                TEXT,
        region              TEXT,
        country             TEXT,
        ticket_url          TEXT,
        event_url           TEXT,
        lineup              TEXT,               -- JSON list of names
        description         TEXT,
        raw_json            TEXT,
        first_imported_at   TEXT NOT NULL,
        last_imported_at    TEXT NOT NULL,
        missing_from_source INTEGER NOT NULL DEFAULT 0,

        -- Project tag. Import only changes it while project_source = 'auto'.
        project             TEXT,               -- NULL means unassigned
        project_source      TEXT NOT NULL DEFAULT 'auto',  -- 'auto' or 'manual'
        project_reason      TEXT,

        -- Filled in by hand; import never touches these.
        ad_budget_cents     INTEGER,
        tickets_sold        INTEGER,
        notes               TEXT,
        ticket_url_override TEXT,
        updated_at          TEXT,

        UNIQUE (source, source_event_id)
    );
    CREATE INDEX gigs_starts_at ON gigs (starts_at);
    """,
]


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    migrate(conn)
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    for number, sql in enumerate(MIGRATIONS[version:], start=version + 1):
        conn.executescript(sql)
        conn.execute(f"PRAGMA user_version = {number}")
    conn.commit()
