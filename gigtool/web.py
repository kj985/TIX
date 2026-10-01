"""The local dashboard (a small Flask web app on http://localhost:5050)."""
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for

from . import SAMPLE_EVENTS_PATH
from .config import ConfigError, load_config
from .db import connect
from .gigs import delete_source, get_gig, list_gigs, set_project, update_manual_fields
from .importer import run_bandsintown_import, run_sample_import
from .sources.bandsintown import BandsintownError

WHEN_OPTIONS = [("upcoming", "Upcoming"), ("past", "Past"), ("all", "All")]


def parse_money_to_cents(text: str) -> int | None:
    text = text.strip().replace("$", "").replace(",", "")
    if not text:
        return None
    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise ValueError("Ad budget must be a number, e.g. 250 or 250.50.")
    if amount < 0:
        raise ValueError("Ad budget can't be negative.")
    return int((amount * 100).quantize(Decimal("1")))


def parse_count(text: str) -> int | None:
    text = text.strip().replace(",", "")
    if not text:
        return None
    if not text.isdigit():
        raise ValueError("Tickets sold must be a whole number, e.g. 312.")
    return int(text)


def parse_url(text: str) -> str | None:
    text = text.strip()
    if not text:
        return None
    if not text.startswith(("http://", "https://")):
        raise ValueError("Ticket link must start with http:// or https://")
    return text


def safe_next(target: str | None, default: str) -> str:
    # Only redirect back to pages inside this app.
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return default


def days_label(days: int) -> str:
    if days == 0:
        return "Today"
    if days == 1:
        return "Tomorrow"
    if days == -1:
        return "Yesterday"
    return f"{days} days" if days > 0 else f"{-days} days ago"


def create_app(base_dir: Path, db_path: Path) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    @app.before_request
    def load_state():
        # Settings are re-read on every page load, so edits to config.toml
        # (e.g. new keywords) apply without restarting.
        try:
            g.config = load_config(base_dir)
        except ConfigError as e:
            return render_template("error.html", message=str(e)), 500
        g.conn = connect(db_path)
        g.today = g.config.today()

    @app.teardown_request
    def close_db(_exc):
        conn = g.pop("conn", None)
        if conn is not None:
            conn.close()

    @app.context_processor
    def helpers():
        config = g.get("config")
        names = config.project_names if config else []
        return {
            "config": config,
            "project_names": names,
            "project_colour": lambda name: (names.index(name) % 6) + 1 if name in names else 0,
            "days_label": days_label,
            "safe_next": safe_next,
        }

    @app.template_filter("money")
    def money(value):
        return "" if value is None else f"${value:,.2f}"

    @app.template_filter("nice_date")
    def nice_date(dt):
        return f"{dt:%a} {dt.day} {dt:%b %Y}"

    @app.template_filter("nice_time")
    def nice_time(dt):
        hour = dt.hour % 12 or 12
        return f"{hour}:{dt:%M}{'am' if dt.hour < 12 else 'pm'}"

    @app.get("/")
    def index():
        when = request.args.get("when", "upcoming")
        if when not in dict(WHEN_OPTIONS):
            when = "upcoming"
        project = request.args.get("project", "")
        gigs = list_gigs(g.conn, g.today, when, project)
        totals = {
            "count": len(gigs),
            "budget": sum(x.ad_budget or 0 for x in gigs),
            "sold": sum(x.tickets_sold or 0 for x in gigs),
            "has_sample": g.conn.execute(
                "SELECT 1 FROM gigs WHERE source = 'sample' LIMIT 1"
            ).fetchone() is not None,
            "any": g.conn.execute("SELECT 1 FROM gigs LIMIT 1").fetchone() is not None,
        }
        return render_template(
            "index.html", gigs=gigs, when=when, project=project,
            when_options=WHEN_OPTIONS, totals=totals,
        )

    def _gig_or_404(gig_id):
        gig = get_gig(g.conn, gig_id, g.today)
        if gig is None:
            abort(404)
        return gig

    def _valid_project_choice(choice: str, gig) -> bool:
        return choice in ("__auto__", "__none__") or choice in g.config.project_names or (
            choice == gig.project
        )

    @app.post("/gigs/<int:gig_id>/project")
    def change_project(gig_id):
        gig = _gig_or_404(gig_id)
        choice = request.form.get("project", "")
        if _valid_project_choice(choice, gig):
            set_project(g.conn, gig_id, choice, g.config)
        return redirect(safe_next(request.form.get("next"), url_for("index")))

    @app.route("/gigs/<int:gig_id>", methods=["GET", "POST"])
    def edit_gig(gig_id):
        gig = _gig_or_404(gig_id)
        form = request.form
        if request.method == "POST":
            try:
                budget = parse_money_to_cents(form.get("ad_budget", ""))
                sold = parse_count(form.get("tickets_sold", ""))
                override = parse_url(form.get("ticket_url_override", ""))
            except ValueError as e:
                flash(str(e), "error")
                return render_template("gig.html", gig=gig, form=form), 400

            choice = form.get("project", "")
            current = "__auto__" if gig.project_source == "auto" else (gig.project or "__none__")
            if choice != current and _valid_project_choice(choice, gig):
                set_project(g.conn, gig_id, choice, g.config)
            update_manual_fields(
                g.conn, gig_id, budget, sold, form.get("notes", "").strip(), override
            )
            flash("Saved.", "ok")
            return redirect(safe_next(request.form.get("next"), url_for("index")))
        return render_template("gig.html", gig=gig, form=None)

    @app.post("/import")
    def do_import():
        try:
            result = run_bandsintown_import(g.conn, g.config)
            flash(f"Imported from Bandsintown: {result.summary()}.", "ok")
        except BandsintownError as e:
            flash(f"Import failed: {e}", "error")
        return redirect(url_for("index"))

    @app.post("/import-sample")
    def do_import_sample():
        result = run_sample_import(g.conn, g.config, SAMPLE_EVENTS_PATH)
        flash(f"Loaded sample gigs: {result.summary()}.", "ok")
        return redirect(url_for("index"))

    @app.post("/clear-sample")
    def do_clear_sample():
        flash(f"Deleted {delete_source(g.conn, 'sample')} sample gigs.", "ok")
        return redirect(url_for("index"))

    return app
