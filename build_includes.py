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
NAV_PATTERN = re.compile(
    r"<!-- BEGIN_NAV -->.*?<!-- END_NAV -->",
    re.DOTALL
)
FOOTER_PATTERN = re.compile(
    r"<!-- BEGIN_FOOTER -->.*?<!-- END_FOOTER -->",
    re.DOTALL
)

verbose = "-v" in sys.argv


def rewrite_paths_for_subdir(html_text):
    """Rewrite root-relative paths to ../  for pages in subdirectories.

    Converts href="index.html" → href="../index.html"
    Converts src="img/logo.jpg" → src="../img/logo.jpg"
    Does NOT touch absolute URLs (http://, https://, //, #, mailto:, tel:).
    """
    def _fix(match):
        attr = match.group(1)   # href= or src=
        quote = match.group(2)  # " or '
        path = match.group(3)   # the path value
        # Skip absolute URLs, anchors, javascript:, mailto:, tel:
        if path.startswith(("http://", "https://", "//", "#", "mailto:", "tel:", "javascript:", "data:")):
            return match.group(0)
        # Skip already-relative paths (starts with ../)
        if path.startswith("../"):
            return match.group(0)
        return f'{attr}{quote}../{path}{quote}'

    return re.sub(r'((?:href|src|action)=)(["\'])([^"\']*)\2', _fix, html_text)


# ── Collect all HTML files (root + subdirectories) ────────────────────────────
html_files = sorted(BASE.glob("*.html"))
# Add subdirectory pages (shows/, etc.) but exclude includes/
for subdir in sorted(BASE.iterdir()):
    if subdir.is_dir() and subdir.name not in ("includes", "css", "js", "img", ".git", "node_modules"):
        html_files.extend(sorted(subdir.glob("*.html")))

# ── Process all HTML files ────────────────────────────────────────────────────
updated = []
skipped = []

for html_file in html_files:
    original = html_file.read_text()
    content = original

    # Determine if file is in a subdirectory
    is_subdir = html_file.parent != BASE

    # Prepare include content (rewrite paths for subdirs)
    nav_content = rewrite_paths_for_subdir(nav_html.strip()) if is_subdir else nav_html.strip()
    footer_content = rewrite_paths_for_subdir(footer_html.strip()) if is_subdir else footer_html.strip()

    # Replace nav
    if "<!-- BEGIN_NAV -->" in content:
        content = NAV_PATTERN.sub(nav_content, content)

    # Replace footer
    if "<!-- BEGIN_FOOTER -->" in content:
        content = FOOTER_PATTERN.sub(footer_content, content)

    rel_path = html_file.relative_to(BASE)
    if content != original:
        html_file.write_text(content)
        updated.append(str(rel_path))
        if verbose:
            print(f"  ✓ {rel_path}")
    else:
        skipped.append(str(rel_path))
        if verbose:
            print(f"  · {rel_path} (no change)")

print(f"build_includes: {len(updated)} updated, {len(skipped)} unchanged")
if updated:
    print(f"  Updated: {', '.join(updated)}")
