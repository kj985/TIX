import tempfile
import unittest
from datetime import date
from pathlib import Path

from gigtool import BASE_DIR, SAMPLE_EVENTS_PATH
from gigtool.config import load_config
from gigtool.db import connect
from gigtool.gigs import get_gig, list_gigs, set_project, update_manual_fields
from gigtool.importer import import_events
from gigtool.sources.bandsintown import encode_artist_name, parse_event
from gigtool.sources.sample import load_sample_events

TODAY = date(2026, 10, 1)


def raw(event_id="1", when="2026-11-01T20:00:00", title="", venue="Corner Hotel", lineup=None):
    return {
        "id": event_id,
        "datetime": when,
        "title": title,
        "description": "",
        "url": "https://example.com/e/1",
        "venue": {"name": venue, "city": "Richmond", "region": "VIC", "country": "Australia"},
        "offers": [{"type": "Tickets", "url": "https://example.com/t/1"}],
        "lineup": lineup or ["Sarah McLeod"],
    }


class ImporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = connect(Path(self.tmp.name) / "test.db")
        self.config = load_config(BASE_DIR)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def run_import(self, raws, source="bandsintown"):
        return import_events(self.conn, source, [parse_event(r) for r in raws], self.config, TODAY)

    def only_gig(self):
        gigs = list_gigs(self.conn, TODAY, "all")
        self.assertEqual(len(gigs), 1)
        return gigs[0]

    def test_reimport_updates_bandsintown_fields_but_keeps_manual_ones(self):
        self.run_import([raw(title="The Superjesus")])
        gig = self.only_gig()
        update_manual_fields(self.conn, gig.id, 25000, 312, "Poster run done", None)

        result = self.run_import([raw(title="The Superjesus", venue="Corner Hotel (moved upstairs)")])
        self.assertEqual((result.added, result.updated), (0, 1))
        gig = self.only_gig()
        self.assertEqual(gig.venue_name, "Corner Hotel (moved upstairs)")
        self.assertEqual(gig.ad_budget_cents, 25000)
        self.assertEqual(gig.tickets_sold, 312)
        self.assertEqual(gig.notes, "Poster run done")

    def test_manual_project_survives_reimport(self):
        self.run_import([raw(title="The Superjesus")])
        gig = self.only_gig()
        set_project(self.conn, gig.id, "Sarah & Mick", self.config)
        self.run_import([raw(title="The Superjesus")])
        gig = self.only_gig()
        self.assertEqual((gig.project, gig.project_source), ("Sarah & Mick", "manual"))

    def test_auto_project_is_redetected_and_can_be_reset(self):
        self.run_import([raw(title="")])
        self.assertEqual(self.only_gig().project, "Sarah McLeod")
        self.run_import([raw(title="Sarah & Mick")])
        gig = self.only_gig()
        self.assertEqual(gig.project, "Sarah & Mick")

        set_project(self.conn, gig.id, "__none__", self.config)
        self.assertIsNone(self.only_gig().project)
        set_project(self.conn, gig.id, "__auto__", self.config)
        self.assertEqual(self.only_gig().project, "Sarah & Mick")

    def test_missing_upcoming_gig_is_flagged_not_deleted(self):
        self.run_import([raw("1"), raw("2", when="2026-12-01T20:00:00")])
        result = self.run_import([raw("1")])
        self.assertEqual(result.flagged_missing, 1)
        gigs = list_gigs(self.conn, TODAY, "all")
        self.assertEqual(len(gigs), 2)
        self.assertEqual([g.missing_from_source for g in gigs], [0, 1])

        self.run_import([raw("1"), raw("2", when="2026-12-01T20:00:00")])
        self.assertEqual([g.missing_from_source for g in list_gigs(self.conn, TODAY, "all")], [0, 0])

    def test_past_gigs_are_not_flagged_when_they_drop_off(self):
        self.run_import([raw("1", when="2026-09-01T20:00:00")])
        self.assertEqual(self.run_import([]).flagged_missing, 0)

    def test_days_until_and_filters(self):
        self.run_import([raw("1", when="2026-10-04T20:00:00"), raw("2", when="2026-09-20T20:00:00")])
        upcoming = list_gigs(self.conn, TODAY, "upcoming")
        self.assertEqual([g.days_until for g in upcoming], [3])
        self.assertEqual([g.days_until for g in list_gigs(self.conn, TODAY, "past")], [-11])

    def test_sample_data_loads_and_is_detected(self):
        events = load_sample_events(SAMPLE_EVENTS_PATH, TODAY)
        import_events(self.conn, "sample", events, self.config, TODAY)
        gigs = list_gigs(self.conn, TODAY, "all")
        self.assertEqual(len(gigs), 13)
        self.assertEqual(gigs[2].days_until, 3)
        self.assertEqual({g.project for g in gigs}, {"The Superjesus", "Sarah & Mick", "Sarah McLeod"})
        no_ticket = [g for g in gigs if g.ticket_url is None]
        self.assertEqual(len(no_ticket), 1)

    def test_get_gig_effective_ticket_url_prefers_override(self):
        self.run_import([raw()])
        gig = self.only_gig()
        update_manual_fields(self.conn, gig.id, None, None, "", "https://example.com/direct")
        self.assertEqual(get_gig(self.conn, gig.id, TODAY).effective_ticket_url, "https://example.com/direct")


class BandsintownParsingTests(unittest.TestCase):
    def test_artist_name_encoding(self):
        self.assertEqual(encode_artist_name("Sarah McLeod"), "Sarah%20McLeod")
        self.assertEqual(encode_artist_name("AC/DC"), "AC%252FDC")

    def test_prefers_ticket_offer(self):
        r = raw()
        r["offers"] = [{"type": "VIP", "url": "https://vip"}, {"type": "Tickets", "url": "https://tix"}]
        self.assertEqual(parse_event(r).ticket_url, "https://tix")

    def test_starts_at_field_and_no_offers(self):
        r = raw()
        del r["datetime"]
        r["starts_at"] = "2026-11-01T20:00:00"
        r["offers"] = []
        ev = parse_event(r)
        self.assertEqual(ev.starts_at, "2026-11-01T20:00:00")
        self.assertIsNone(ev.ticket_url)


if __name__ == "__main__":
    unittest.main()
