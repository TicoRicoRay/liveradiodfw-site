"""Offline regression tests: python -m unittest test_build_mtv_setlist."""
from contextlib import redirect_stdout
from datetime import date
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

import build_mtv_setlist as mtv
import build_songs


PAGE = """<h1>Leave the design alone</h1>
<!-- BEGIN_MTV_COUNT -->2 selections<!-- END_MTV_COUNT -->
<!-- BEGIN_MTV_SETLIST -->old<!-- END_MTV_SETLIST -->
<!-- BEGIN_MTV_DATE -->September 23, 2026<!-- END_MTV_DATE -->
<form>Leave the booking form alone</form>"""


def song(name="Money For Nothing", artist="Dire Straits"):
    return {"type": "song", "name": name, "artist": artist, "key": "PRIVATE"}


class MTVTests(unittest.TestCase):
    def test_order_labels_and_extras(self):
        items = [
            {"type": "set", "name": "Set 1"}, song(),
            song("Video Killed the Radio Star", "The Buggles"),
            {"type": "set", "name": "Extra's"}, song("Birthday", "Beatles"),
        ]
        result = mtv.parse_feed(items)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "I Want My MTV / Money for Nothing")
        self.assertEqual(result[1][1], "The Buggles")

    def test_multiple_sets_and_extras_variants(self):
        for extra in ("Extra", "Extras", "Extra's", "Extra\u2019s"):
            result = mtv.parse_feed([
                song(), {"type": "set", "name": extra}, song("Not public", "X"),
                {"type": "set", "name": "Set 2"}, song("Second set", "Y")
            ])
            self.assertEqual([s[0] for s in result], [
                "I Want My MTV / Money for Nothing", "Second set"
            ])

    def test_invalid_and_empty_feed(self):
        for value in (None, {}, [], [None], [song("", "Artist")],
                      [song("Title", None)], [{"type": "oops"}],
                      [{"type": "set", "name": "Extras"}, song()]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                mtv.parse_feed(value)

    def test_escapes_public_fields_and_omits_metadata(self):
        result = mtv.parse_feed([song("Don&#039;t <script>x</script>", "Hall &amp; Oates")])
        rendered = mtv.render_list(result)
        self.assertIn("Don&#x27;t &lt;script&gt;x&lt;/script&gt;", rendered)
        self.assertIn("Hall &amp; Oates", rendered)
        self.assertNotIn("PRIVATE", rendered)

    def test_membership_and_order_follow_source_not_a_fixed_song_count(self):
        songs = mtv.parse_feed([song("B", "Artist"), song("A", "Artist"), song("C", "Artist")])
        updated = mtv.update_page(PAGE, songs, date(2026, 9, 24))
        self.assertIn("3 selections", updated)
        self.assertIn("--setlist-rows:2", updated)
        self.assertLess(updated.index(">B<"), updated.index(">A<"))
        self.assertIn("September 24, 2026", updated)
        smaller = mtv.update_page(updated, songs[:1], date(2026, 9, 25))
        self.assertIn("1 selection", smaller)
        self.assertNotIn(">C<", smaller)

    def test_noop_preserves_date_and_unrelated_design(self):
        songs = mtv.parse_feed([song()])
        first = mtv.update_page(PAGE, songs, date(2026, 9, 23))
        self.assertEqual(first, mtv.update_page(first, songs, date(2026, 10, 5)))
        self.assertIn("<h1>Leave the design alone</h1>", first)
        self.assertIn("<form>Leave the booking form alone</form>", first)

    def test_bad_markers_fail_closed(self):
        for text in (PAGE.replace("BEGIN_MTV_DATE", "MISSING"),
                     PAGE + "<!-- BEGIN_MTV_COUNT -->",
                     PAGE.replace("BEGIN_MTV_SETLIST", "END_MTV_SETLIST", 1)):
            with self.assertRaises(ValueError):
                mtv.update_page(text, [("Song", "Artist")])

    def test_failed_fetch_or_json_leaves_last_good_page(self):
        with tempfile.TemporaryDirectory() as folder:
            page = Path(folder) / "index.html"
            page.write_text(PAGE, encoding="utf-8")
            for exc in (requests.Timeout("test"), ValueError("bad JSON")):
                with self.assertRaises(type(exc)):
                    mtv.sync_setlist(page, fetch=Mock(side_effect=exc))
                self.assertEqual(page.read_text(encoding="utf-8"), PAGE)
            response = Mock(content=b"[]")
            response.json.return_value = []
            with self.assertRaises(ValueError):
                mtv.sync_setlist(page, fetch=Mock(return_value=response))
            self.assertEqual(page.read_text(encoding="utf-8"), PAGE)

    def test_atomic_write_then_noop(self):
        with tempfile.TemporaryDirectory() as folder:
            page = Path(folder) / "index.html"
            page.write_text(PAGE, encoding="utf-8")
            response = Mock(content=b"test")
            response.json.return_value = [song()]
            fetch = Mock(return_value=response)
            self.assertTrue(mtv.sync_setlist(page, fetch=fetch))
            self.assertFalse(mtv.sync_setlist(page, fetch=fetch))
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])
            self.assertEqual(fetch.call_args.kwargs["timeout"], 20)

    def test_mtv_only_update_appears_in_daily_sync_summary(self):
        for changed, expected in ((True, "Updated : 1  (mtv)"), (False, "Cached  : 1  (mtv)")):
            output = io.StringIO()
            with tempfile.TemporaryDirectory() as cache, \
                    patch.object(build_songs, "CACHE_DIR", cache), \
                    patch.object(build_songs, "URLS", {}), \
                    patch.object(build_songs, "PAGE_MAP", {}), \
                    patch.object(build_songs, "load_hashes", return_value={}), \
                    patch.object(build_songs, "sync_setlist", return_value=changed), \
                    redirect_stdout(output):
                build_songs.main()
            self.assertIn(expected, output.getvalue())

    def test_mtv_failure_is_reported_to_daily_sync(self):
        with tempfile.TemporaryDirectory() as cache, \
                patch.object(build_songs, "CACHE_DIR", cache), \
                patch.object(build_songs, "URLS", {}), \
                patch.object(build_songs, "PAGE_MAP", {}), \
                patch.object(build_songs, "load_hashes", return_value={}), \
                patch.object(build_songs, "sync_setlist", side_effect=ValueError("bad feed")), \
                redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
            build_songs.main()
        self.assertEqual(raised.exception.code, 1)

    def test_other_feed_failure_defers_mtv_write(self):
        with tempfile.TemporaryDirectory() as cache, \
                patch.object(build_songs, "CACHE_DIR", cache), \
                patch.object(build_songs, "URLS", {"all": "https://example.invalid"}), \
                patch.object(build_songs, "PAGE_MAP", {}), \
                patch.object(build_songs, "load_hashes", return_value={}), \
                patch.object(build_songs.requests, "get", side_effect=requests.Timeout("test")), \
                patch.object(build_songs, "sync_setlist") as sync, \
                redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            build_songs.main()
        sync.assert_not_called()


if __name__ == "__main__":
    unittest.main()
