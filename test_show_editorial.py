"""Editorial show details survive sync and render without affecting other shows."""
import json
from pathlib import Path
import unittest

from build_show_pages import build_show_page
from sync_lib import merge_calendar_fields


class EditorialShowTests(unittest.TestCase):
    def setUp(self):
        data = json.loads(Path(__file__).with_name("shows.json").read_text(encoding="utf-8"))
        self.show = next(s for s in data if s["date"] == "2026-10-10")

    def test_paragraphs_heading_and_official_links(self):
        _, page = build_show_page(self.show)
        self.assertIn("Live Radio DFW Opens Plano", page)
        self.assertIn("Live Radio DFW is opening for Hard Night's Day", page)
        self.assertEqual(page.count('<p style="margin-top:var(--space-4)">'), 3)
        self.assertIn('>Get Tickets</a>', page)
        self.assertIn('>Official Event Details</a>', page)
        self.assertIn(self.show["ticket_url"], page)
        self.assertIn(self.show["event_url"], page)

    def test_editorial_fields_survive_calendar_merge(self):
        result = merge_calendar_fields(self.show, dict(self.show, time="7:00 PM"))
        for key in ("description", "page_heading", "meta_description", "ticket_url", "event_url"):
            self.assertEqual(result[key], self.show[key])

    def test_draft_and_unsafe_link_not_published(self):
        show = dict(self.show, ticket_url="javascript:alert(1)")
        _, page = build_show_page(show)
        self.assertNotIn("javascript:alert(1)", page)
        _, page = build_show_page(dict(show, description="[DRAFT] Unapproved words"))
        self.assertNotIn("Unapproved words", page)
        self.assertNotIn(">Get Tickets</a>", page)


if __name__ == "__main__":
    unittest.main()
