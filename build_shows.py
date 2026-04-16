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
from pathlib import Path

BASE = Path(__file__).parent

# ── Load shows ────────────────────────────────────────────────────────────────
with open(BASE / "shows.json") as f:
    all_shows = json.load(f)

# Always sort the full list by date and write it back (prevents out-of-order JSON)
all_shows.sort(key=lambda s: s["date"])
with open(BASE / "shows.json", "w") as f:
    json.dump(all_shows, f, indent=2)
    f.write("\n")

# Filter out past shows for upcoming display
today = date.today()
upcoming = [s for s in all_shows if datetime.strptime(s["date"], "%Y-%m-%d").date() >= today]

PRIVATE_BADGE = '<p class="show-private-badge" style="display:inline-block;margin-top:0.25rem;padding:2px 10px;font-size:var(--text-xs);font-weight:600;color:#e63946;border:1px solid #e63946;border-radius:999px;text-transform:uppercase;letter-spacing:0.05em;">Private Event</p>'

# ── Build shows.html show-card-full blocks ────────────────────────────────────
def build_full_cards(shows):
    lines = []
    for s in shows:
        is_private = s.get("private", False)
        lines.append(f'      <div class="show-card-full fade-in" data-show-date="{s["date"]}">')
        lines.append(f'        <div class="show-date-badge">')
        lines.append(f'          <span class="day-name">{s["day_name"]}</span>')
        lines.append(f'          <span class="day-num">{s["day_num"]}</span>')
        lines.append(f'          <span class="month">{s["month"]}</span>')
        lines.append(f'        </div>')
        lines.append(f'        <div class="show-details">')
        ticket_price = s.get("ticket_price", "Free")
        price_label = "Free" if ticket_price == "Free" else ticket_price
        price_class = "show-price-free" if ticket_price == "Free" else "show-price-paid"
        price_html = f'<span class="show-ticket-price {price_class}">{price_label}</span>'
        if is_private:
            lines.append(f'          <h3>Private Event</h3>')
            lines.append(f'          <p class="venue-address">{s["address_short"]}</p>')
            lines.append(f'          <p class="show-time">{s["time"]}</p>')
            lines.append(f'          {PRIVATE_BADGE}')
        else:
            lines.append(f'          <h3>{s["title"]}</h3>')
            lines.append(f'          <p class="venue-address">{s["venue"]}, {s["address"]}</p>')
            lines.append(f'          <p class="show-time">{s["time"]} &middot; {price_html}</p>')
            lines.append(f'          <div class="show-links">')
            lines.append(f'            <a href="{s["maps_url"]}" target="_blank" rel="noopener">View on Google Maps</a>')
            share_text = f'Live Radio DFW at {s["title"]}'
            lines.append(f'            <button data-share="{share_text}" style="background:none;border:none;color:var(--text-secondary);font-size:var(--text-xs);cursor:pointer;text-decoration:underline;">Share</button>')
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
        lines.append(f'        <div class="show-date-badge">')
        lines.append(f'          <span class="day-name">{s["day_name"]}</span>')
        lines.append(f'          <span class="day-num">{s["day_num"]}</span>')
        lines.append(f'          <span class="month">{s["month"]}</span>')
        lines.append(f'        </div>')
        lines.append(f'        <div class="show-details">')
        ticket_price = s.get("ticket_price", "Free")
        price_label = "Free" if ticket_price == "Free" else ticket_price
        price_class = "show-price-free" if ticket_price == "Free" else "show-price-paid"
        price_html = f'<span class="show-ticket-price {price_class}">{price_label}</span>'
        if is_private:
            lines.append(f'          <h3>Private Event</h3>')
            lines.append(f'          <p class="venue-address">{s["address_short"]}</p>')
            lines.append(f'          <p class="show-time">{s["time"]}</p>')
        else:
            lines.append(f'          <h3>{s["title"]}</h3>')
            lines.append(f'          <p class="venue-address">{s["address_short"]}</p>')
            lines.append(f'          <p class="show-time">{s["time"]} &middot; {price_html}</p>')
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

# Replace JSON-LD
jsonld_new = build_jsonld(all_shows)
shows_html = re.sub(
    r'(<script type="application/ld\+json">)\s*\[.*?\]\s*(</script>)',
    lambda m: m.group(1) + jsonld_new + m.group(2),
    shows_html,
    flags=re.DOTALL
)

# Replace show cards between markers
full_cards = build_full_cards(all_shows)
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

print(f"\nShows in JSON: {len(all_shows)} total, {len(upcoming)} upcoming")
for s in upcoming:
    flag = " [PRIVATE]" if s.get("private", False) else ""
    print(f"  {s['date']}  {s['title']}{flag}")
