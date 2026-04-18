#!/usr/bin/env python3
"""
build_show_pages.py — LiveRadioDFW individual show page builder
================================================================
Generates individual HTML pages for each public show in shows.json.
These pages target local SEO queries like "live music at [venue] [city]".

Output directory: shows/
Filename pattern:  shows/{venue-slug}-{YYYY-MM-DD}.html

Private events are skipped (no SEO value, no public details).
Past shows are kept (backlink value, proof of activity).

Each page includes:
  - Full SEO meta (title, description, canonical, Open Graph)
  - JSON-LD MusicEvent structured data
  - Nav/footer markers for build_includes.py
  - Show details (venue, date, time, address, map link, ticket price)
  - Placeholder for show description (Ray approves before publishing)
  - Link back to full shows page
  - Breadcrumb navigation

Called automatically by sync_calendar.py after build_shows.py.

Usage:
    python build_show_pages.py          # build all pages
    python build_show_pages.py -v       # verbose
"""

import json
import re
import sys
from datetime import datetime
from html import escape as html_escape
from pathlib import Path

BASE = Path(__file__).parent
SHOWS_DIR = BASE / "shows"
SHOWS_DIR.mkdir(exist_ok=True)

VERBOSE = "-v" in sys.argv


def slugify(text):
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[''`]", "", text)           # remove apostrophes
    text = re.sub(r"[^a-z0-9]+", "-", text)     # non-alphanum → dash
    text = re.sub(r"-+", "-", text)             # collapse multiple dashes
    return text.strip("-")


def parse_time_to_iso(date_str, time_str):
    """Convert date + time string to ISO datetime."""
    try:
        time_str = time_str.upper().strip()
        is_pm = "PM" in time_str
        is_am = "AM" in time_str
        clean = time_str.replace("PM", "").replace("AM", "").strip()
        parts = clean.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        if is_pm and hour != 12:
            hour += 12
        if is_am and hour == 12:
            hour = 0
        return f"{date_str}T{hour:02d}:{minute:02d}:00"
    except (ValueError, IndexError):
        return f"{date_str}T20:00:00"


def format_long_date(date_str):
    """Convert 2026-04-18 to "Friday April 18, 2026" (no comma after the
    weekday, per Ray 2026-04-18)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%A %B %d, %Y").replace(" 0", " ")


def build_show_page(show):
    """Generate full HTML for a single show page."""
    venue = show["venue"]
    title = show["title"]
    date_str = show["date"]
    time_str = show["time"]
    address = show["address"]
    address_short = show["address_short"]
    maps_url = show["maps_url"]
    ticket_price = show.get("ticket_price", "Free")
    description = show.get("description", "")
    # "past" shows (historic imports or dates that have rolled by) get a subtle
    # banner and drop the forward-looking CTAs (Add-to-Calendar, Share). The
    # page itself still exists for SEO / backlink value.
    is_past = bool(show.get("past"))
    try:
        if not is_past:
            show_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            is_past = show_date < datetime.now().date()
    except ValueError:
        pass

    # HTML-safe versions for use in data attributes
    venue_attr = html_escape(venue, quote=True)
    address_attr = html_escape(address, quote=True)

    long_date = format_long_date(date_str)
    iso_datetime = parse_time_to_iso(date_str, time_str)

    # SEO fields
    page_title = f"Live Radio DFW at {venue} · {long_date} | Live Music {address_short}"
    meta_desc = (
        f"Catch Live Radio DFW live at {venue} in {address_short} on {long_date}. "
        f"{'Free admission. ' if ticket_price == 'Free' else f'{ticket_price} admission. '}"
        f"High-energy 70s, 80s, classic rock, and oldies cover band."
    )
    # Trim meta description to ~155 chars
    if len(meta_desc) > 160:
        meta_desc = meta_desc[:157] + "..."

    slug = slugify(venue)
    filename = f"{slug}-{date_str}.html"
    canonical = f"https://liveradiodfw.com/shows/{filename}"

    # Price display
    if ticket_price == "Free":
        price_html = '<span class="show-ticket-price show-price-free">Free</span>'
    else:
        price_html = f'<span class="show-ticket-price show-price-paid">{ticket_price}</span>'

    # Description section. Three states:
    #   1. Approved description present — render the About This Show block.
    #   2. Draft placeholder (string starts with "[DRAFT") — never publish
    #      draft text to the public site; fall through to the placeholder.
    #   3. No description at all — render a short "Show details coming soon"
    #      placeholder (B16 Stage 1) so the page has a visible signal that
    #      more content is on the way instead of silently-thin content.
    desc_section = ""
    approved = description and not description.lstrip().startswith("[DRAFT")
    if approved:
        desc_section = f"""
      <div class="show-page-description">
        <h2>About This Show</h2>
        <p>{description}</p>
      </div>"""
    else:
        desc_section = """
      <div class="show-page-description show-page-description-placeholder">
        <h2>About This Show</h2>
        <p>Show details coming soon. In the meantime, see the date, time, and location above or reach out via the Contact page.</p>
      </div>"""

    # JSON-LD. For past shows, drop the Offer (ticket availability is moot)
    # and still emit MusicEvent since Google accepts historic events for
    # archival/knowledge graph purposes.
    jsonld_obj = {
        "@context": "https://schema.org",
        "@type": "MusicEvent",
        "name": f"Live Radio DFW at {title}",
        "startDate": iso_datetime,
        "location": {
            "@type": "Place",
            "name": venue,
            "address": address
        },
        "performer": {
            "@type": "MusicGroup",
            "name": "Live Radio DFW",
            "url": "https://liveradiodfw.com"
        },
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
    }
    if not is_past:
        jsonld_obj["offers"] = {
            "@type": "Offer",
            "price": "0" if ticket_price == "Free" else ticket_price.replace("$", ""),
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "url": canonical,
        }
    jsonld = json.dumps(jsonld_obj, indent=2)

    # Past-show banner + trimmed actions. Keep "Get Directions" (useful for
    # anyone revisiting the venue) and "All Shows" link; drop
    # Add-to-Calendar and Share-as-event (not meaningful for past shows).
    past_banner_html = ""
    if is_past:
        past_banner_html = (
            '\n    <div class="show-page-past-banner" '
            'style="margin:1rem 0;padding:0.5rem 1rem;background:var(--color-bg-subtle,#f5f5f5);'
            'border-left:3px solid var(--color-accent,#e63946);font-size:var(--text-sm);'
            'color:var(--color-text-muted,#555);">'
            f'This show took place on {long_date}. '
            '<a href="../past-shows.html">See all past shows</a>.'
            '</div>'
        )

    if is_past:
        actions_html = (
            f'<a href="{maps_url}" target="_blank" rel="noopener" class="btn btn-secondary">Get Directions</a>\n'
            f'        <a href="../past-shows.html" class="btn btn-secondary">All Past Shows</a>\n'
            f'        <a href="../shows.html" class="btn btn-secondary">Upcoming Shows</a>'
        )
    else:
        actions_html = (
            f'<button class="btn-share btn-primary" data-share="Live Radio DFW at {venue_attr} - {long_date}" data-share-url="{canonical}">'
            f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>'
            f'<line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg> Share</button>\n'
            f'        <a href="{maps_url}" target="_blank" rel="noopener" class="btn btn-secondary">Get Directions</a>\n'
            f'        <button class="btn-calendar" data-cal-title="Live Radio DFW at {venue_attr}" data-cal-date="{date_str}" data-cal-time="{time_str}" data-cal-venue="{venue_attr}" data-cal-address="{address_attr}" data-cal-url="{canonical}">'
            f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg> Add to Calendar</button>\n'
            f'        <a href="../shows.html" class="btn btn-secondary">All Shows</a>'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <script>!function(){{var e=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';document.documentElement.setAttribute('data-theme',e)}}();</script>
  <link rel="icon" href="../favicon.ico" sizes="any">
  <link rel="icon" href="../img/favicon-32.png" type="image/png">
  <link rel="apple-touch-icon" href="../img/apple-touch-icon.png">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <meta name="description" content="{meta_desc}">
  <link rel="canonical" href="{canonical}">

  <!-- Open Graph -->
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:image" content="https://liveradiodfw.com/img/logo.jpg">
  <meta property="og:url" content="{canonical}">
  <meta property="og:type" content="website">

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

  <!-- Styles -->
  <link rel="stylesheet" href="../css/style.css?v=40">
  <script type="application/ld+json">{jsonld}</script>
</head>
<body>
<!-- BEGIN_NAV -->
<!-- END_NAV -->

<main class="content-wrap">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="../index.html">Home</a> &rsaquo;
    <a href="../shows.html">Shows</a> &rsaquo;
    <span>{venue} &mdash; {long_date}</span>
  </nav>

  <section class="show-page-hero">
    <div class="show-page-date">
      <span class="day-name">{show["day_name"]}</span>
      <span class="day-num">{show["day_num"]}</span>
      <span class="month">{show["month"]}</span>
    </div>
    <div class="show-page-info">
      <h1>Live Radio DFW at {venue}</h1>
      <p class="show-page-meta"><span class="show-full-date">{long_date}</span> &middot; {time_str} &middot; {price_html}</p>
      <p class="show-page-venue">{venue}</p>
      <p class="show-page-address">{address}</p>
      <div class="show-page-actions">
        {actions_html}
      </div>
    </div>
  </section>{past_banner_html}
{desc_section}
</main>

<!-- BEGIN_FOOTER -->
<!-- END_FOOTER -->
<script src="../js/main.js?v=2"></script>
<script src="../js/show-actions.js"></script>
</body>
</html>"""

    return filename, html


def main():
    # Load shows
    with open(BASE / "shows.json") as f:
        shows = json.load(f)

    # Track what we build
    built = []
    skipped = []

    for show in shows:
        # Skip private events
        if show.get("private", False):
            skipped.append(show["date"] + " " + show.get("title", "Private"))
            continue

        filename, html = build_show_page(show)
        filepath = SHOWS_DIR / filename
        filepath.write_text(html, encoding="utf-8")
        built.append(filename)
        if VERBOSE:
            print(f"  ✓ shows/{filename}")

    # Clean up pages for shows that no longer exist in shows.json
    # (only remove auto-generated pages, identified by matching the naming pattern)
    expected_files = set(built)
    for existing in SHOWS_DIR.glob("*.html"):
        if existing.name not in expected_files:
            existing.unlink()
            if VERBOSE:
                print(f"  ✗ removed shows/{existing.name} (no longer in shows.json)")

    print(f"✓ show pages: {len(built)} built, {len(skipped)} private (skipped)")


if __name__ == "__main__":
    main()
