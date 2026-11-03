import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from website_placeholders import load_placeholders


class WebsitePlaceholderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "placeholders.json"
        self.entries = [
            {"date": "2026-12-05", "time": "7:00 PM"},
            {"date": "2026-12-12", "time": "7:00 PM"},
        ]
        self.path.write_text(json.dumps(self.entries), encoding="utf-8")

    def test_private_cards_without_booking_details(self):
        cards = load_placeholders(self.path, [], date(2026, 11, 3))
        self.assertEqual([c["date"] for c in cards], ["2026-12-05", "2026-12-12"])
        for card in cards:
            self.assertTrue(card["private"])
            self.assertTrue(card["website_placeholder"])
            self.assertEqual(card["day_name"], "Sat")
            self.assertEqual(card["time"], "7:00 PM")
            self.assertEqual(card["address"], "")
            self.assertEqual(card["maps_url"], "")

    def test_real_booking_wins_and_is_not_modified(self):
        real = [{"date": "2026-12-05", "title": "Real booking"}]
        cards = load_placeholders(self.path, real, date(2026, 11, 3))
        self.assertEqual([c["date"] for c in cards], ["2026-12-12"])
        self.assertEqual(real, [{"date": "2026-12-05", "title": "Real booking"}])

    def test_expired_cards_disappear(self):
        self.assertEqual(len(load_placeholders(self.path, [], date(2026, 12, 6))), 1)
        self.assertEqual(load_placeholders(self.path, [], date(2026, 12, 13)), [])

    def test_missing_file_is_optional(self):
        self.assertEqual(load_placeholders(self.path.with_name("missing.json"), []), [])

    def test_duplicate_dates_only_render_once(self):
        self.path.write_text(json.dumps(self.entries * 2), encoding="utf-8")
        self.assertEqual(len(load_placeholders(self.path, [], date(2026, 11, 3))), 2)

    def test_invalid_time_rejected(self):
        self.path.write_text('[{"date":"2026-12-05","time":"bad"}]', encoding="utf-8")
        with self.assertRaises(ValueError):
            load_placeholders(self.path, [], date(2026, 11, 3))


if __name__ == "__main__":
    unittest.main()
