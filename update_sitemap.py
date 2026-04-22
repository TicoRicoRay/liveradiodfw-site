#!/usr/bin/env python3
"""
update_sitemap.py -- regenerate the /shows/ entries in sitemap.xml to match
the actual files in shows/. Leaves the static (non-show) entries alone.
"""

import re
from pathlib import Path

BASE = Path(__file__).parent
SITEMAP = BASE / "sitemap.xml"
SHOWS_DIR = BASE / "shows"
SITE = "https://liveradiodfw.com"

def main():
    # Collect all show pages present on disk
    pages = sorted([p.name for p in SHOWS_DIR.glob("*.html")])

    xml = SITEMAP.read_text()

    # Strip all existing /shows/*.html <url> blocks
    pattern = re.compile(
        r"  <url><loc>" + re.escape(SITE) + r"/shows/[^<]+</loc>[^<]*"
        r"<priority>[^<]+</priority>[^<]*"
        r"<changefreq>[^<]+</changefreq></url>\n"
    )
    xml = pattern.sub("", xml)

    # Append the fresh block just before </urlset>
    new_entries = "".join(
        f'  <url><loc>{SITE}/shows/{name}</loc>'
        f'<priority>0.5</priority>'
        f'<changefreq>yearly</changefreq></url>\n'
        for name in pages
    )
    xml = xml.replace("</urlset>", new_entries + "</urlset>")

    SITEMAP.write_text(xml)
    print(f"OK sitemap.xml updated: {len(pages)} show pages")

if __name__ == "__main__":
    main()
