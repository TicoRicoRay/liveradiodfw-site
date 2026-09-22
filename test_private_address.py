"""Private event street addresses must not enter public show records."""

import unittest

from sync_lib import calendar_event_to_show, detail_diffs, merge_calendar_fields


class PrivateAddressTests(unittest.TestCase):
    def event(self, title="LR - Private Event"):
        return {
            "title": title,
            "start": "2026-10-16T23:00:00Z",
            "location": "Example Venue, 123 Example Road, Allen, TX 75013",
            "description": "",
        }

    def test_private_address_removed_without_changing_calendar_input(self):
        event = self.event()
        original = dict(event)
        show = calendar_event_to_show(event)
        self.assertEqual(show["address"], "")
        self.assertEqual(show["maps_url"], "")
        self.assertEqual(show["address_short"], "Allen, TX")
        self.assertEqual(show["title"], "Private Event")
        self.assertTrue(show["private"])
        self.assertEqual(event, original)

    def test_existing_address_is_detected_and_cleared_on_sync(self):
        fresh = calendar_event_to_show(self.event())
        existing = dict(fresh, address="123 Example Road", description="Keep this")
        self.assertIn(("address", "123 Example Road", ""), detail_diffs(existing, fresh))
        merged = merge_calendar_fields(existing, fresh)
        self.assertEqual(merged["address"], "")
        self.assertEqual(merged["description"], "Keep this")

    def test_public_address_and_map_are_preserved(self):
        show = calendar_event_to_show(self.event("LR - Example Venue"))
        self.assertFalse(show["private"])
        self.assertEqual(show["address"], "123 Example Road, Allen, TX 75013")
        self.assertTrue(show["maps_url"].startswith("https://maps.google.com/"))


if __name__ == "__main__":
    unittest.main()
