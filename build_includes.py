#!/usr/bin/env python3
"""
build_includes.py — LiveRadioDFW static include builder
========================================================
Single point of maintenance for nav and footer across all pages.

Source of truth:
    includes/nav.html       — site navigation + mobile overlay
    includes/footer.html    — site footer (contact, social, copyright)

How it works:
    1. Reads the include templates from includes/
    2. Scans all .html files in the site root (excludes includes/ dir)
    3. Replaces content between markers with the current template:
         Nav:    <!-- BEGIN_NAV --> ... <!-- END_NAV -->
         Footer: <!-- BEGIN_FOOTER --> ... <!-- END_FOOTER -->
    4. Reports what changed

Usage:
    python build_includes.py          # update all pages
    python build_includes.py -v       # verbose — show each file

Called automatically by sync_calendar.py after build_shows.py.
"""

import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
INCLUDES = BASE / "includes"

# ── Load templates ────────────────────────────────────────────────────────────
nav_html = (INCLUDES / "nav.html").read_text()
footer_html = (INCLUDES / "footer.html").read_text()

# ── Regex patterns for replacement ────────────────────────────────────────────
# Nav: everything between BEGIN_NAV and END_NAV comments (inclusive)
NAV_PATTERN = re.compile(
    r"<!-- BEGIN_NAV -->.*?<!-- END_NAV -->",
    re.DOTALL
)

# Footer: everything between BEGIN_FOOTER and END_FOOTER comments (inclusive)
FOOTER_PATTERN = re.compile(
    r"<!-- BEGIN_FOOTER -->.*?<!-- END_FOOTER -->",
    re.DOTALL
)

verbose = "-v" in sys.argv

# ── Process all HTML files ────────────────────────────────────────────────────
updated = []
skipped = []

for html_file in sorted(BASE.glob("*.html")):
    original = html_file.read_text()
    content = original

    # Replace nav
    if "<!-- BEGIN_NAV -->" in content:
        content = NAV_PATTERN.sub(nav_html.strip(), content)

    # Replace footer
    if "<!-- BEGIN_FOOTER -->" in content:
        content = FOOTER_PATTERN.sub(footer_html.strip(), content)

    if content != original:
        html_file.write_text(content)
        updated.append(html_file.name)
        if verbose:
            print(f"  ✓ {html_file.name}")
    else:
        skipped.append(html_file.name)
        if verbose:
            print(f"  · {html_file.name} (no change)")

print(f"build_includes: {len(updated)} updated, {len(skipped)} unchanged")
if updated:
    print(f"  Updated: {', '.join(updated)}")
