"""Reading and editing gigs. The dashboard (and later, the Meta ads and
click-tracking code) should go through these functions rather than writing
SQL directly."""
import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone

from .config import Config
from .projects import detect_project


@dataclass
class Gig:
    row: sqlite3.Row
    today: date

    def __getattr__(self, name):
        return self.row[name]

    @property
    def starts(self) -> datetime:
        return datetime.fromisoformat(self.row["starts_at"])

    @property
    def days_until(self) -> int:
        return (self.starts.date() - self.today).days

    @property
    def is_past(self) -> bool:
        return self.days_until < 0

    @property
    def effective_ticket_url(self) -> str | None:
        return self.row["ticket_url_override"] or self.row["ticket_url"]

    @property
    def lineup_list(self) -> list[str]:
        return json.loads(self.row["lineup"] or "[]")

    @property
    def ad_budget(self) -> float | None:
        cents = self.row["ad_budget_cents"]
        return None if cents is None else cents / 100

    @property
    def location(self) -> str:
        return ", ".join(p for p in (self.row["city"], self.row["region"]) if p)


def list_gigs(
    conn: sqlite3.Connection, today: date, when: str = "upcoming", project: str = ""
) -> list[Gig]:
    """when: 'upcoming', 'past' or 'all'. project: a name, '__none__' for
    unassigned, or '' for all projects."""
    sql = "SELECT * FROM gigs WHERE 1 = 1"
    params: list = []
    if when == "upcoming":
        sql += " AND starts_at >= ?"
        params.append(today.isoformat())
    elif when == "past":
        sql += " AND starts_at < ?"
        params.append(today.isoformat())
    if project == "__none__":
        sql += " AND project IS NULL"
    elif project:
        sql += " AND project = ?"
        params.append(project)
    sql += " ORDER BY starts_at " + ("DESC" if when == "past" else "ASC")
    return [Gig(row, today) for row in conn.execute(sql, params)]


def get_gig(conn: sqlite3.Connection, gig_id: int, today: date) -> Gig | None:
    row = conn.execute("SELECT * FROM gigs WHERE id = ?", (gig_id,)).fetchone()
    return Gig(row, today) if row else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def set_project(conn: sqlite3.Connection, gig_id: int, choice: str, config: Config) -> None:
    """choice: a project name, '__none__' (unassigned), or '__auto__' to go
    back to automatic detection."""
    if choice == "__auto__":
        row = conn.execute(
            "SELECT title, lineup, description FROM gigs WHERE id = ?", (gig_id,)
        ).fetchone()
        detection = detect_project(
            row["title"], json.loads(row["lineup"] or "[]"), row["description"],
            config.projects, config.fallback_project,
        )
        values = (detection.project, "auto", detection.reason)
    elif choice == "__none__":
        values = (None, "manual", "Set by hand")
    else:
        values = (choice, "manual", "Set by hand")
    conn.execute(
        "UPDATE gigs SET project = ?, project_source = ?, project_reason = ?, updated_at = ? "
        "WHERE id = ?",
        (*values, _now(), gig_id),
    )
    conn.commit()


def update_manual_fields(
    conn: sqlite3.Connection,
    gig_id: int,
    ad_budget_cents: int | None,
    tickets_sold: int | None,
    notes: str,
    ticket_url_override: str | None,
) -> None:
    conn.execute(
        """UPDATE gigs SET ad_budget_cents = ?, tickets_sold = ?, notes = ?,
                  ticket_url_override = ?, updated_at = ?
           WHERE id = ?""",
        (ad_budget_cents, tickets_sold, notes, ticket_url_override, _now(), gig_id),
    )
    conn.commit()


def delete_source(conn: sqlite3.Connection, source: str) -> int:
    cur = conn.execute("DELETE FROM gigs WHERE source = ?", (source,))
    conn.commit()
    return cur.rowcount
