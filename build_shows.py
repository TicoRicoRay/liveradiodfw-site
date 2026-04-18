#!/usr/bin/env python3
"""
build_shows.py — LiveRadioDFW show data builder
================================================
Source of truth: shows.json
Stamps HTML into:  shows.html   (full show-card-full blocks)
                   index.html   (compact show-card blocks, next 3 upcoming)

Run this script any time shows.json is updated.
It will be called automatically by the cron that adds new shows.

Usage:
    python build_shows.py
"""

import json
import re
from datetime import date, datetime
from html import escape as html_escape
from pathlib import Path

BASE = Path(__file__).parent


def format_full_date(date_str):
    """Return "Saturday April 25, 2026" from an ISO date string.
    No comma after the weekday (per Ray's spec 2026-04-18).
    Renders above the time on every show card."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return date_str
    return dt.strftime("%A %B %d, %Y").replace(" 0", " ")


def slugify(text):
    """Convert text to URL-friendly slug (matches build_show_pages.py)."""
    text = text.lower().strip()
    text = re.sub(r"[''`]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


# ── Load shows ────────────────────────────────────────────────────────────────
with open(BASE / "shows.json") as f:
    all_shows = json.load(f)

# Always sort the full list by date and write it back (prevents out-of-order JSON)
all_shows.sort(key=lambda s: s["date"])
with open(BASE / "shows.json", "w") as f:
    json.dump(all_shows, f, indent=2)
    f.write("\n")

# Filter out past shows for upcoming display.
# A show is past when its date is before today OR when it carries the explicit
# "past": true flag (set by import_bandzoogle.py for historic imports).
today = date.today()


def is_past(s):
    if s.get("past") is True:
        return True
    return datetime.strptime(s["date"], "%Y-%m-%d").date() < today


upcoming = [s for s in all_shows if not is_past(s)]
past_shows = [s for s in all_shows if is_past(s)]
# past-shows list is rendered reverse-chronologically (most recent first).
past_shows_rev = sorted(past_shows, key=lambda s: s["date"], reverse=True)

PRIVATE_BADGE = '<p class="show-private-badge" style="display:inline-block;margin-top:0.25rem;padding:2px 10px;font-size:var(--text-xs);font-weight:600;color:#e63946;border:1px solid #e63946;border-radius:999px;text-transform:uppercase;letter-spacing:0.05em;">Private Event</p>'

# ── Build shows.html show-card-full blocks ────────────────────────────────────
def build_full_cards(shows):
    lines = []
    for s in shows:
        is_private = s.get("private", False)
        lines.append(f'      <div class="show-card-full fade-in" data-show-date="{s["date"]}">')
        if not is_private:
            slug = slugify(s['venue'])
            show_page_url = f'shows/{slug}-{s["date"]}.html'
            lines.append(f'        <a href="{show_page_url}" class="show-date-badge">')
        else:
            lines.append(f'        <div class="show-date-badge">')
        lines.append(f'          <span class="day-name">{s["day_name"]}</span>')
        lines.append(f'          <span class="day-num">{s["day_num"]}</span>')
        lines.append(f'          <span class="month">{s["month"]}</span>')
        lines.append(f'        </{'a' if not is_private else 'div'}>')
        lines.append(f'        <div class="show-details">')
        ticket_price = s.get("ticket_price", "Free")
        price_label = "Free" if ticket_price == "Free" else ticket_price
        price_class = "show-price-free" if ticket_price == "Free" else "show-price-paid"
        price_html = f'<span class="show-ticket-price {price_class}">{price_label}</span>'
        full_date = format_full_date(s["date"])
        full_date_html = f'<span class="show-full-date">{full_date}</span>'
        if is_private:
            lines.append(f'          <h3>Private Event</h3>')
            lines.append(f'          <p class="venue-address">{s["address_short"]}</p>')
            lines.append(f'          <p class="show-time">{full_date_html} &middot; {s["time"]}</p>')
            lines.append(f'          {PRIVATE_BADGE}')
        else:
            lines.append(f'          <h3><a href="{show_page_url}">{s["title"]}</a></h3>')
            # B10 render fix: the h3 title above already carries venue/event name.
            # Showing venue name again as a prefix on the address line duplicates it
            # (especially visible when title is just the venue, e.g. "Frisco Rail Yard").
            # Render street address only. `address` in shows.json is already cleaned
            # of any leading venue segment by sync_calendar.py.
            lines.append(f'          <p class="venue-address">{s["address"]}</p>')
            lines.append(f'          <p class="show-time">{full_date_html} &middot; {s["time"]} &middot; {price_html}</p>')
            lines.append(f'          <div class="show-links">')
            lines.append(f'            <a href="{show_page_url}">Show Details</a>')
            lines.append(f'            <a href="{s["maps_url"]}" target="_blank" rel="noopener">Directions</a>')
            # Past shows: no Add-to-Calendar (pointless) and no Share (event already happened)
            if not is_past(s):
                venue_esc = html_escape(s['venue'], quote=True)
                addr_esc = html_escape(s['address'], quote=True)
                title_esc = html_escape(s['title'], quote=True)
                cal_title = f'Live Radio DFW at {venue_esc}'
                lines.append(f'            <button class="btn-share-inline" data-cal-title="{cal_title}" data-cal-date="{s["date"]}" data-cal-time="{s["time"]}" data-cal-venue="{venue_esc}" data-cal-address="{addr_esc}">Add to Calendar</button>')
                share_text = f'Live Radio DFW at {title_esc}'
                share_url = f'https://liveradiodfw.com/{show_page_url}'
                lines.append(f'            <button class="btn-share-inline" data-share="{share_text}" data-share-url="{share_url}">Share</button>')
            lines.append(f'          </div>')
        lines.append(f'        </div>')
        lines.append(f'      </div>')
    return "\n".join(lines)

# ── Build index.html compact show-card blocks (next 3) ───────────────────────
def build_compact_cards(shows):
    lines = []
    for s in shows[:3]:
        is_private = s.get("private", False)
        lines.append(f'      <div class="show-card fade-in">')
        if not is_private:
            slug = slugify(s['venue'])
            show_page_url = f'shows/{slug}-{s["date"]}.html'
            lines.append(f'        <a href="{show_page_url}" class="show-date-badge">')
        else:
            lines.append(f'        <div class="show-date-badge">')
        lines.append(f'          <span class="day-name">{s["day_name"]}</span>')
        lines.append(f'          <span class="day-num">{s["day_num"]}</span>')
        lines.append(f'          <span class="month">{s["month"]}</span>')
        lines.append(f'        </{'a' if not is_private else 'div'}>')
        lines.append(f'        <div class="show-details">')
        ticket_price = s.get("ticket_price", "Free")
        price_label = "Free" if ticket_price == "Free" else ticket_price
        price_class = "show-price-free" if ticket_price == "Free" else "show-price-paid"
        price_html = f'<span class="show-ticket-price {price_class}">{price_label}</span>'
        full_date = format_full_date(s["date"])
        full_date_html = f'<span class="show-full-date">{full_date}</span>'
        if is_private:
            lines.append(f'          <h3>Private Event</h3>')
            lines.append(f'          <p class="venue-address">{s["address_short"]}</p>')
            lines.append(f'          <p class="show-time">{full_date_html} &middot; {s["time"]}</p>')
        else:
            lines.append(f'          <h3><a href="{show_page_url}">{s["title"]}</a></h3>')
            lines.append(f'          <p class="venue-address">{s["address_short"]}</p>')
            lines.append(f'          <p class="show-time">{full_date_html} &middot; {s["time"]} &middot; {price_html}</p>')
        lines.append(f'        </div>')
        lines.append(f'      </div>')
    return "\n".join(lines)

# ── Build JSON-LD MusicEvent blocks for shows.html ───────────────────────────
def build_jsonld(shows):
    events = []
    for s in shows:
        # Skip private events — no SEO benefit
        if s.get("private", False):
            continue
        try:
            time_str = s["time"].upper().strip()
            is_pm = "PM" in time_str
            is_am = "AM" in time_str
            clean = time_str.replace("PM", "").replace("AM", "").strip()
            time_parts = clean.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            if is_pm and hour != 12:
                hour += 12
            if is_am and hour == 12:
                hour = 0
            start_dt = f'{s["date"]}T{hour:02d}:{minute:02d}:00'
        except (ValueError, IndexError):
            start_dt = f'{s["date"]}T20:00:00'  # default 8pm if time is unparseable
        event = {
            "@context": "https://schema.org",
            "@type": "MusicEvent",
            "name": f'Live Radio DFW at {s["title"]}',
            "startDate": start_dt,
            "location": {
                "@type": "Place",
                "name": s["venue"],
                "address": s["address"]
            },
            "performer": {
                "@type": "MusicGroup",
                "name": "Live Radio DFW",
                "url": "https://www.liveradiodfw.com"
            },
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode"
        }
        events.append(event)
    return json.dumps(events, indent=2)

# ── Stamp shows.html ──────────────────────────────────────────────────────────
shows_html_path = BASE / "shows.html"
shows_html = shows_html_path.read_text(encoding="utf-8")

# Replace JSON-LD. JSON-LD MusicEvent entries are for upcoming shows only;
# past events already happened and Google's event markup is for discovery.
jsonld_new = build_jsonld(upcoming)
shows_html = re.sub(
    r'(<script type="application/ld\+json">)\s*\[.*?\]\s*(</script>)',
    lambda m: m.group(1) + jsonld_new + m.group(2),
    shows_html,
    flags=re.DOTALL
)

# Replace show cards between markers. Only upcoming shows appear on /shows
# (past shows get their own /past-shows.html page, built separately).
full_cards = build_full_cards(upcoming)
shows_html = re.sub(
    r'(<!-- BEGIN_SHOWS -->).*?(<!-- END_SHOWS -->)',
    lambda m: m.group(1) + "\n" + full_cards + "\n    " + m.group(2),
    shows_html,
    flags=re.DOTALL
)
shows_html_path.write_text(shows_html, encoding="utf-8")
print("✓ shows.html updated")

# ── Stamp index.html ──────────────────────────────────────────────────────────
index_html_path = BASE / "index.html"
index_html = index_html_path.read_text(encoding="utf-8")

compact_cards = build_compact_cards(upcoming)
index_html = re.sub(
    r'(<!-- BEGIN_SHOWS -->).*?(<!-- END_SHOWS -->)',
    lambda m: m.group(1) + "\n" + compact_cards + "\n    " + m.group(2),
    index_html,
    flags=re.DOTALL
)
index_html_path.write_text(index_html, encoding="utf-8")
print("✓ index.html updated")

# ── Stamp past-shows.html ────────────────────────────────────────────────────────────
# past-shows.html is a separate index page showing every past show in
# reverse-chronological order. It only exists once there is at least one
# past show (the template file is written by hand; the shows are stamped
# into the BEGIN_SHOWS/END_SHOWS markers here).
past_shows_html_path = BASE / "past-shows.html"
if past_shows_html_path.exists() and past_shows_rev:
    past_html = past_shows_html_path.read_text(encoding="utf-8")
    past_cards = build_full_cards(past_shows_rev)
    past_html = re.sub(
        r'(<!-- BEGIN_SHOWS -->).*?(<!-- END_SHOWS -->)',
        lambda m: m.group(1) + "\n" + past_cards + "\n    " + m.group(2),
        past_html,
        flags=re.DOTALL
    )
    past_shows_html_path.write_text(past_html, encoding="utf-8")
    print(f"✓ past-shows.html updated ({len(past_shows_rev)} past shows)")

print(f"\nShows in JSON: {len(all_shows)} total, {len(upcoming)} upcoming, {len(past_shows)} past")
for s in upcoming:
    flag = " [PRIVATE]" if s.get("private", False) else ""
    print(f"  {s['date']}  {s['title']}{flag}")
