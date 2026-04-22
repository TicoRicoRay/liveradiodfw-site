#!/usr/bin/env python3
"""
import_historic.py -- one-time historic Google Calendar import (R16)
===================================================================
Reads approved_historic.json (produced by build_approved_historic.py from
Ray's Tier 1/Tier 2 approvals) and merges those 63 past shows into
shows.json with:

  - schema matching existing shows.json entries exactly
  - "past": true
  - "source": "calendar-historic-import-2026-04-18"
  - venue normalization (canonical names + full addresses)
  - prior-band-name sanitization (Jackson Crossing / Risky Business -> Live Radio DFW)
  - description strategy (B16 Stage 1, same as import_bandzoogle.py):
      * calendar description >= 50 chars after sanitization -> use verbatim
      * otherwise -> generate_description_draft() which prefixes [DRAFT - ...]
        and is gated by build_show_pages.py so it never auto-publishes

Dedupe: any date already present in shows.json is skipped. Existing earliest
show in shows.json is 2024-08-09; approved historic events are 2021-04 to
2024-07, so no collisions expected, but guard anyway.

Usage:
    python3 import_historic.py --dry-run   # print summary, no write
    python3 import_historic.py             # writes shows.json (with .bak)
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sync_lib import generate_description_draft  # noqa: E402
from import_bandzoogle import (  # noqa: E402
    sanitize_prior_band_names,
    should_regenerate_description,
    format_time,
)

BASE = Path(__file__).parent
APPROVED = BASE / "approved_historic.json"
SHOWS = BASE / "shows.json"
SOURCE_TAG = "calendar-historic-import-2026-04-18"

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Canonical venue map. Keys lowercased; matched by substring against title
# and location. Built from Tier 1 + Tier 2 approvals.
VENUE_MATCHERS = [
    # (lowercase match against title+location, canonical_venue, canonical_address)
    ("frisco bar",            "The Frisco Bar & Grill",            "6750 Gaylord Pkwy ste.120, Frisco, TX 75034, USA"),
    ("box garden at legacy hall", "The Box Garden at Legacy Hall", "7800 Windrose Ave, Plano, TX 75024, USA"),
    ("watters creek",          "Watters Creek Village",             "970 Garden Park Dr, Allen, TX 75013, USA"),
    ("lion & crown, 932",      "Lion & Crown Pub - Allen",          "932 Garden Park Dr, Allen, TX 75013, USA"),
    ("lion & crown, 5001",     "Lion & Crown Pub - Addison",        "5001 Addison Cir, Addison, TX 75001, USA"),
    ("lion & crown\n5001",     "Lion & Crown Pub - Addison",        "5001 Addison Cir, Addison, TX 75001, USA"),
    ("addison cir",            "Lion & Crown Pub - Addison",        "5001 Addison Cir, Addison, TX 75001, USA"),
    ("lion & crown allen",     "Lion & Crown Pub - Allen",          "932 Garden Park Dr, Allen, TX 75013, USA"),
    ("lion & crown addison",   "Lion & Crown Pub - Addison",        "5001 Addison Cir, Addison, TX 75001, USA"),
    ("harvest hall",           "Harvest Hall",                      "815 S Main St, Grapevine, TX 76051, USA"),
    ("third rail",             "Harvest Hall - Third Rail",         "815 S Main St, Grapevine, TX 76051, USA"),
    ("fresh by brookshire",    "FRESH by Brookshire's",             "5100 I-30, Fate, TX 75189, USA"),
    ("powder creek",           "Powder Creek Pavilion",             "520 S Center St, Bonham, TX 75418, USA"),
    ("sweetwater grill",       "Sweetwater Grill",                  "4884 TX-276, Royse City, TX 75189, USA"),
    ("rockin' s bar and grill at twin coves", "Rockin' S at Twin Coves", "4600 Wilson Rd, Flower Mound, TX 75022, USA"),
    ("rockin' s bar and grill at hidden cove", "Rockin' S Hidden Cove", "20400 Hackberry Creek Pk Rd #100, The Colony, TX 75056, USA"),
    ("village dallas",         "The Village Dallas",                "5605 Village Glen Dr, Dallas, TX 75206, USA"),
    ("shakertins",             "Shakertins Prosper",                "1140 S Preston Rd #30, Prosper, TX 75078, USA"),
    ("charlie's lakeside",     "Charlie's Lakeside Bar & Grill",    "1481 E Hill Park Rd, Lewisville, TX 75057, USA"),
    # Tier 2 new venues
    ("plano sports tavern",    "Plano Sports Tavern",               "3000 Custer Rd #345, Plano, TX 75075, USA"),
    ("american legion post 597","American Legion Post 597",         "1024 S Elm St, Carrollton, TX 75006, USA"),
    ("maverick",               "The Maverick",                      "1616 W Hebron Pkwy #108, Carrollton, TX 75010, USA"),
    ("howling mutt",           "Howling Mutt Brewing",              "205 N Cedar St, Denton, TX 76201, USA"),
    ("lava cantina",           "Lava Cantina The Colony",           "5805 Grandscape Blvd, The Colony, TX 75056, USA"),
    ("turning point beer",     "Turning Point Beer",                "1307 Brown Trail, Bedford, TX 76022, USA"),
    ("johnny krackers",        "Johnny Krackers",                   "501 E Moore Ave, Terrell, TX 75160, USA"),
    ("harry myers park",       "Harry Myers Park",                  "815 E Washington St, Rockwall, TX 75087, USA"),
    ("horsemen",               "Horsemen's Bar-B-Que",              "1680 S State Hwy 121, Lewisville, TX 75067, USA"),
    # Private-marked venues that we still want to identify (for internal notes only)
    ("rusted rail",            "Rusted Rail Golf, Grill, & Events", "1602 US-175, Crandall, TX 75114, USA"),
]


def match_venue(title, location):
    """Return (canonical_venue, canonical_address) or (None, None)."""
    hay = f"{title}\n{location}".lower()
    # Special-case Lion & Crown: must check Addison before plain "lion & crown"
    # because the Addison address contains "5001" and the Allen contains "932".
    if "5001 addison" in hay or "addison cir" in hay or "lion & crown addison" in hay:
        return "Lion & Crown Pub - Addison", "5001 Addison Cir, Addison, TX 75001, USA"
    if "932 garden park" in hay or "lion & crown allen" in hay:
        return "Lion & Crown Pub - Allen", "932 Garden Park Dr, Allen, TX 75013, USA"
    for needle, venue, addr in VENUE_MATCHERS:
        if needle in hay:
            return venue, addr
    return None, None


def build_address_short(address):
    """Produce \"City, TX\" from a full address string."""
    if not address:
        return ""
    parts = [p.strip() for p in address.split(",")]
    # Standard form: "street, city, TX ZIP, USA" -- take parts[-3] and TX from [-2]
    if len(parts) >= 3:
        city = parts[-3]
        state_zip = parts[-2]
        # Extract state (TX)
        state = state_zip.strip().split()[0] if state_zip.strip() else "TX"
        return f"{city}, {state}"
    return parts[-1] if parts else ""


def build_maps_url(venue, address):
    if not address:
        return ""
    q = f"{venue}, {address}" if venue and not address.startswith(venue) else address
    return "https://maps.google.com/?q=" + q.replace(" ", "+").replace(",", "%2C")


def extract_time(start_iso):
    """Events stored as UTC in raw JSON. Convert to America/Chicago 12-hour."""
    # start like "2021-04-17T02:00:00.000Z" -> UTC 02:00 = Central 21:00 (CDT) day before
    # We'll use zoneinfo for accuracy across DST.
    from datetime import datetime, timezone
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo
    s = start_iso.replace("Z", "+00:00")
    dt_utc = datetime.fromisoformat(s)
    dt_ct = dt_utc.astimezone(ZoneInfo("America/Chicago"))
    h = dt_ct.hour
    m = dt_ct.minute
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {ap}", dt_ct.date()


def import_entry(ev):
    """Convert one approved_historic.json entry into a shows.json entry."""
    title = (ev.get("title") or "").strip()
    location = (ev.get("location") or "").strip()
    raw_desc = (ev.get("description") or "")
    privacy = ev.get("privacy", "public")
    private = (privacy == "private")

    # Determine time and local date
    time_str, local_date = extract_time(ev["start"])
    date_str = local_date.strftime("%Y-%m-%d")
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    day_name = DAY_NAMES[dt.weekday()]
    day_num = str(dt.day)
    month = MONTHS[dt.month - 1]

    if private:
        # Present privately: no street address, no venue name
        address_short = "DFW Area"
        # Try to pull a city from location if possible
        if location:
            # "..., City, TX ZIP, USA"
            parts = [p.strip() for p in location.split(",")]
            if len(parts) >= 3:
                city = parts[-3]
                address_short = f"{city}, TX"
        show_title = "Private Event"
        venue = "Private Event"
        address = ""
        maps_url = ""
        ticket_price = ""
    else:
        venue, address = match_venue(title, location)
        if not venue:
            # Fall back to cleaned title + raw location
            venue = title if title else "TBA"
            address = location
        address_short = build_address_short(address) if address else ""
        maps_url = build_maps_url(venue, address)
        ticket_price = "Free"  # Default matches dominant pattern
        show_title = venue

    # Historic Google Calendar descriptions are always internal band notes
    # (booking fees, contact names, gate codes, load-in instructions, etc).
    # Unlike Bandzoogle "past show" copy which was written for the public,
    # these cannot ship verbatim. Always regenerate via the [DRAFT - ...]
    # template -- build_show_pages.py gates drafts so they never reach the
    # public site. Ray can enrich them later post-import.
    description = generate_description_draft({
        "private": private,
        "venue": venue,
        "address_short": address_short,
        "ticket_price": ticket_price,
        "time": time_str,
        "day_name": day_name,
        "date": date_str,
    })

    return {
        "date": date_str,
        "day_name": day_name,
        "day_num": day_num,
        "month": month,
        "title": show_title,
        "venue": venue,
        "address": address,
        "address_short": address_short,
        "time": time_str,
        "maps_url": maps_url,
        "private": private,
        "ticket_price": ticket_price,
        "description": description,
        "past": True,
        "source": SOURCE_TAG,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Print summary to stdout, do not write shows.json")
    parser.add_argument("--inspect", action="store_true",
                        help="Print every imported entry (for eyeball review)")
    args = parser.parse_args()

    approved = json.loads(APPROVED.read_text())
    existing = json.loads(SHOWS.read_text())
    existing_dates = {s["date"] for s in existing}

    imported = []
    skipped_dedupe = []
    for ev in approved:
        entry = import_entry(ev)
        if entry["date"] in existing_dates:
            skipped_dedupe.append(entry["date"])
            continue
        imported.append(entry)

    merged = existing + imported
    merged.sort(key=lambda s: s["date"])

    # Report
    print(f"Existing shows.json: {len(existing)} entries")
    print(f"Approved historic:   {len(approved)} entries")
    print(f"Imported:            {len(imported)} (past=True)")
    print(f"Skipped (dedupe):    {len(skipped_dedupe)} {skipped_dedupe if skipped_dedupe else ''}")
    print(f"Merged total:        {len(merged)} entries")
    print()

    drafts = [s for s in imported if (s.get("description") or "").startswith("[DRAFT")]
    verbatim = [s for s in imported
                if s.get("description")
                and not s.get("description", "").startswith("[DRAFT")
                and not s.get("private")]
    private_past = [s for s in imported if s.get("private")]
    unmatched_venues = [s for s in imported if not s["private"] and s["venue"] not in {
        v for _, v, _ in VENUE_MATCHERS
    } and s["venue"] not in {"Lion & Crown Pub - Allen", "Lion & Crown Pub - Addison"}]

    print(f"Imported breakdown:")
    print(f"  verbatim descriptions: {len(verbatim)}")
    print(f"  [DRAFT] descriptions:  {len(drafts)}")
    print(f"  private (no desc):     {len(private_past)}")
    print(f"  venues not in canonical map: {len(unmatched_venues)}")
    for u in unmatched_venues:
        print(f"    - {u['date']} | {u['venue']} | {u['address_short']}")

    if args.inspect:
        print("\n--- INSPECT: imported entries ---")
        for s in imported:
            print(f"{s['date']} {s['time']:9s} | priv={s['private']!s:5s} | {s['venue'][:40]:40s} | {s['address_short']}")

    if args.dry_run:
        print("\n(dry run -- shows.json not written)")
        return

    bak = SHOWS.with_suffix(".json.bak2")
    shutil.copy2(SHOWS, bak)
    SHOWS.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"\nOK shows.json updated ({bak.name} saved as backup)")


if __name__ == "__main__":
    main()
