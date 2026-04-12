#!/usr/bin/env python3
"""
build_nav.py — LiveRadioDFW global nav builder
===============================================
Source of truth: nav.html
Stamps nav HTML into all 16 HTML pages between:
  <!-- BEGIN_NAV --> and <!-- END_NAV -->

Also sets the correct .active class on the current page's nav link.

Run this script any time nav.html is updated.

Usage:
    python build_nav.py
"""

import re
from pathlib import Path

BASE = Path(__file__).parent

# Pages and which nav link href should be active for each
PAGE_ACTIVE = {
    'index.html':                            'index.html',
    'shows.html':                            'shows.html',
    'songs.html':                            'songs.html',
    'the-all-80s-hits-station.html':         'songs.html',
    'the-all-70s-no-disco-hits-station.html':'songs.html',
    'the-classic-rock-station.html':         'songs.html',
    'the-all-oldies-hits-station.html':      'songs.html',
    'videos.html':                           'videos.html',
    'about.html':                            'about.html',
    'members.html':                          'members.html',
    'store.html':                            'store.html',
    'book.html':                             None,
    'contact.html':                          None,
    'press-kit.html':                        None,
    'corporate-events.html':                 None,
    'private-parties.html':                  None,
}

# Load nav.html (no active classes — we set them per page)
nav_template = (BASE / 'nav.html').read_text(encoding='utf-8')

def make_nav_for_page(page):
    """Return nav HTML with the correct .active class for this page."""
    active_href = PAGE_ACTIVE.get(page)
    if not active_href:
        return nav_template

    # Set active on the matching nav-links <a>
    # Replace href="active_href" with href="active_href" class="active"
    # But only inside .nav-links (not mobile overlay)
    nav = nav_template

    # Only touch the desktop nav-links ul — split on mobile-overlay to be safe
    parts = nav.split('<div class="mobile-overlay"')
    desktop = parts[0]
    mobile = '<div class="mobile-overlay"' + parts[1] if len(parts) > 1 else ''

    # Add active class to the matching link in desktop nav
    desktop = desktop.replace(
        f'href="{active_href}"',
        f'href="{active_href}" class="active"',
        1  # only first occurrence
    )

    return desktop + mobile

def add_nav_markers_if_missing(content):
    """If a page doesn't have nav markers yet, add them around the existing <nav> block."""
    if '<!-- BEGIN_NAV -->' in content:
        return content
    # Insert markers around the nav + mobile-overlay block
    content = content.replace('<body>\n<nav ', '<body>\n<!-- BEGIN_NAV -->\n<nav ', 1)
    # Find end of mobile-overlay div and insert END_NAV after it
    content = re.sub(
        r'(</div>\n)(</div>\n<div class="page-header"|</div>\n<div class="stats-bar"|</div>\n\n<div class="page-header"|</div>\n\n<section)',
        r'\1<!-- END_NAV -->\n\2',
        content,
        count=1
    )
    return content

updated = 0
for page, active_href in PAGE_ACTIVE.items():
    path = BASE / page
    if not path.exists():
        print(f'  SKIP (not found): {page}')
        continue

    content = path.read_text(encoding='utf-8')

    # Add markers if missing
    content = add_nav_markers_if_missing(content)

    # Build nav for this page
    nav_html = make_nav_for_page(page)

    # Stamp between markers
    new_content = re.sub(
        r'<!-- BEGIN_NAV -->.*?<!-- END_NAV -->',
        '<!-- BEGIN_NAV -->\n' + nav_html + '\n<!-- END_NAV -->',
        content,
        flags=re.DOTALL
    )

    if new_content != content:
        path.write_text(new_content, encoding='utf-8')
        print(f'  updated: {page}')
        updated += 1
    else:
        print(f'  no change: {page}')

print(f'\nDone — {updated} pages updated.')
print('Nav source: nav.html')
print('To update nav: edit nav.html, then run python build_nav.py, then git push.')
