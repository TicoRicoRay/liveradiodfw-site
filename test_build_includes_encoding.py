"""Exercise UTF-8 site building with Windows-style cp1252 defaults."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


BUILDER = Path(__file__).with_name("build_includes.py")
RUNNER = """
from pathlib import Path
import runpy
import sys

original_open = Path.open

def windows_open(self, mode='r', buffering=-1, encoding=None,
                 errors=None, newline=None):
    if 'b' not in mode and encoding in (None, 'locale'):
        encoding = 'cp1252'
    return original_open(self, mode, buffering, encoding, errors, newline)

Path.open = windows_open
runpy.run_path(sys.argv[1], run_name='__main__')
"""


class IncludeEncodingTests(unittest.TestCase):
    def test_utf8_templates_pages_and_idempotency(self):
        # U+201D has UTF-8 byte 0x9d, undefined in cp1252. U+2603 also
        # verifies that output is UTF-8, not merely readable as cp1252.
        text = "Music \u201d caf\u00e9 \u2603"
        for placement in ("nav", "footer", "page"):
            with self.subTest(placement=placement), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                shutil.copyfile(BUILDER, root / BUILDER.name)
                (root / "includes").mkdir()
                (root / "shows").mkdir()
                for name in ("nav", "footer"):
                    content = text if placement == name else name
                    template = (
                        f"<!-- BEGIN_{name.upper()} -->"
                        f'<a href="index.html">{content}</a>'
                        f"<!-- END_{name.upper()} -->"
                    )
                    (root / "includes" / f"{name}.html").write_text(
                        template, encoding="utf-8"
                    )
                page_text = text if placement == "page" else "Show"
                page = (
                    "<html><head></head><body>\n"
                    "<!-- BEGIN_NAV -->old<!-- END_NAV -->\n"
                    f"<p>{page_text}</p>\n"
                    "<!-- BEGIN_FOOTER -->old<!-- END_FOOTER -->\n"
                    "</body></html>\n"
                )
                outputs = [root / "index.html", root / "shows" / "example.html"]
                for path in outputs:
                    path.write_text(page, encoding="utf-8")
                command = [sys.executable, "-c", RUNNER, str(root / BUILDER.name)]
                result = subprocess.run(command, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
                for path in outputs:
                    rendered = path.read_text(encoding="utf-8")
                    self.assertIn(text, rendered)
                    self.assertIn('rel="canonical"', rendered)
                self.assertIn(
                    'href="../index.html"',
                    outputs[1].read_text(encoding="utf-8"),
                )
                sitemap = root / "sitemap.xml"
                self.assertIn(
                    "https://www.liveradiodfw.com/shows/example",
                    sitemap.read_text(encoding="utf-8"),
                )
                before = {p: p.read_bytes() for p in outputs + [sitemap]}
                result = subprocess.run(command, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
                self.assertEqual(before, {p: p.read_bytes() for p in before})


if __name__ == "__main__":
    unittest.main()
