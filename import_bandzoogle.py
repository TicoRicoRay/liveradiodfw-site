#!/usr/bin/env python3
"""
import_bandzoogle.py — one-time Bandzoogle historical shows import (R15)
=========================================================================
Reads bandzoogle_raw.json (extracted 2026-04-18 from the staging calendar
at https://liveradiodfw.bandzoogle.com/shows?calendar_page_prev=1 and =2)
and merges those 33 past shows into shows.json with:

  - schema matching existing shows.json entries exactly
  - "past": true
  - "source": "bandzoogle-import-2026-04-18"
  - venue normalization against the canonical venue names already in
    shows.json (e.g. "Fresh by Brookshires" -> "FRESH by Brookshire's")
  - address normalization (strip leading venue segment, build address_short,
    build maps_url)
  - description strategy (B16 Stage 1):
      * Bandzoogle description >= 50 chars AND not mentioning
        "Jackson Crossing" (prior band name) -> use verbatim
      * otherwise -> generate_description_draft() from sync_calendar.py,
        which prefixes "[DRAFT - ...]" and is gated by build_show_pages.py
        so it never publishes to the public site

Dedupe: entries whose date is already present in shows.json are skipped
(the calendar/shows.json is source of truth for any overlap).

Usage:
    python3 import_bandzoogle.py --dry-run   # prints merged JSON, no write
    python3 import_bandzoogle.py             # writes shows.json in place
                                               (creates shows.json.bak first)
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Re-use the description draft helper from sync_calendar.py so past-show
# drafts match the exact voice calibration B16 Stage 1 already ships.
sys.path.insert(0, str(Path(__file__).parent))
from sync_calendar import generate_description_draft  # noqa: E402

BASE = Path(__file__).parent
RAW = BASE / "bandzoogle_raw.json"
SHOWS = BASE / "shows.json"
SOURCE_TAG = "bandzoogle-import-2026-04-18"

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Canonical venue names (keys are lowercased lookup values).
# Pulled from existing shows.json and sync_calendar output. When a Bandzoogle
# venue_name matches one of these loosely, we replace with the canonical form
# so the site doesn't end up with "Fresh by Brookshires" AND
# "FRESH by Brookshire's" as two separate venues.
VENUE_CANONICAL = {
    "fresh by brookshires": "FRESH by Brookshire's",
    "fresh by brookshire's": "FRESH by Brookshire's",
    "the patio at fresh by brookshires": "FRESH by Brookshire's",
    "frisco rail yard": "Frisco Rail Yard",
    "lion & crown": "Lion & Crown Pub",
    "lion and crown": "Lion & Crown Pub",
    "watters creek": "Watters Creek Village",
    "harvest hall - third rail": "Harvest Hall - Third Rail",
    "harvest hall third rail": "Harvest Hall - Third Rail",
    "the frisco bar & grill": "The Frisco Bar & Grill",
    "lucy's yard": "Lucy's Yard",
    "powder creek pavilion": "Powder Creek Pavilion",
    "charlie's lakeside": "Charlie's Lakeside Bar & Grill",
    "rockin s hidden cove": "Rockin' S Hidden Cove",
}

# Canonical addresses keyed by canonical venue name. Used to fill in a fuller
# address when Bandzoogle only provided a partial (e.g. "Fresh" at
# "Memorial Parkway, Fate, TX" — the correct pin is 5100 I-30).
VENUE_FULL_ADDRESS = {
    "FRESH by Brookshire's": "5100 I-30, Fate, TX 75189, USA",
    "Frisco Rail Yard": "9040 First St, Frisco, TX 75034, USA",
    "Lion & Crown Pub": "932 Garden Park Dr, Allen, TX 75013, USA",
    "Watters Creek Village": "970 Garden Park Dr, Allen, TX 75013, USA",
    "Harvest Hall - Third Rail": "815 S Main St, Grapevine, TX 76051, USA",
    "The Frisco Bar & Grill": "750 Gaylord Pkwy, Frisco, TX 75034, USA",
    "Lucy's Yard": "1070 Watters Creek Blvd, Allen, TX 75013, USA",
    "Powder Creek Pavilion": "522 S Center St, Bonham, TX 75418, USA",
    "Charlie's Lakeside Bar & Grill": "1481 E Hill Park Rd, Lewisville, TX 75057, USA",
    "Rockin' S Hidden Cove": "20400 Hackberry Creek Pk Rd #100, The Colony, TX 75056, USA",
}


def canonicalize_venue(raw_name):
    """Map a Bandzoogle venue_name to the site's canonical form. Falls back
    to the raw name, trimmed."""
    if not raw_name:
        return ""
    key = raw_name.strip().lower()
    return VENUE_CANONICAL.get(key, raw_name.strip())


def build_address_short(city_state, full_address):
    """Produce "City, TX" from the Bandzoogle fields. Bandzoogle's city_state
    is already in that form when present; fall back to parsing full_address."""
    if city_state:
        return city_state.strip()
    if full_address:
        # Best-effort: last two comma-separated parts.
        parts = [p.strip() for p in full_address.split(",")]
        if len(parts) >= 2:
            return ", ".join(parts[-2:])
        return full_address.strip()
    return ""


def build_maps_url(venue, address):
    if not address:
        return ""
    q = f"{venue}, {address}" if venue and not address.startswith(venue) else address
    return "https://maps.google.com/?q=" + q.replace(" ", "+").replace(",", "%2C")


def format_time(time_str):
    """Bandzoogle times are already "7:30 PM" form. Normalize to
    "7:30 PM" (zero-padded minutes) to match sync_calendar output."""
    if not time_str:
        return "TBA"
    s = time_str.strip().upper()
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$", s)
    if not m:
        return time_str.strip()
    h = int(m.group(1))
    mm = m.group(2) or "00"
    ap = m.group(3)
    return f"{h}:{mm} {ap}"


def is_private_from_raw(raw):
    """A Bandzoogle entry is private when the venue/title signals it and
    there's no public street address. Mirrors sync_calendar.is_private_event
    in spirit but works on the raw Bandzoogle fields."""
    title = (raw.get("title") or "").lower()
    venue = (raw.get("venue_name") or "").lower()
    markers = ("private event", "private party", "private birthday",
               "private community")
    if any(m in title for m in markers) or any(m in venue for m in markers):
        return True
    return False


# Prior band names. Same members, different era. Per Ray (2026-04-18):
# the shows DID happen, so we keep them on the timeline, but we strip the
# prior name out of the visible description so the archive presents as a
# single continuous Live Radio DFW brand.
PRIOR_BAND_NAMES = (
    "Jackson Crossing",
    "Risky Business",
)

# Phrasings we swap in when the old band name was the subject of a sentence
# like "rock by the water with Jackson Crossing at Charlie's...". "Live Radio
# DFW" is the safe drop-in that preserves grammar.
PRIOR_BAND_SWAP = "Live Radio DFW"


def sanitize_prior_band_names(text):
    """Replace any mention of a prior band name with the current brand. Does
    case-insensitive whole-word matching so we don't touch unrelated words.
    Returns (cleaned_text, replaced_something_bool)."""
    if not text:
        return text, False
    out = text
    changed = False
    for name in PRIOR_BAND_NAMES:
        pattern = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
        new = pattern.sub(PRIOR_BAND_SWAP, out)
        if new != out:
            changed = True
            out = new
    # Collapse accidental "Live Radio DFW Live Radio DFW" if two prior names
    # were adjacent (belt and suspenders — not expected in the current data).
    out = re.sub(r"(Live Radio DFW)(\s+\1)+", r"\1", out)
    return out, changed


def should_regenerate_description(raw_desc):
    """B16 description strategy for past shows.

    Use verbatim (after prior-band-name sanitization) when:
      - description is present
      - >= 50 chars of actual content

    Otherwise regenerate via generate_description_draft().
    """
    if not raw_desc:
        return True
    text = raw_desc.strip()
    if len(text) < 50:
        return True
    return False


def import_entry(raw):
    """Convert one bandzoogle_raw.json entry into a shows.json entry."""
    date_str = raw["date"]
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    day_name = DAY_NAMES[dt.weekday()]
    day_num = str(dt.day)
    month = MONTHS[dt.month - 1]

    private = is_private_from_raw(raw)

    if private:
        title = "Private Event"
        venue = "Private Event"
        # Public-facing short address. If Bandzoogle gave us a city, keep it;
        # else use "DFW Area" (matches current private-event convention).
        address_short = (raw.get("city_state") or "").strip() or "DFW Area"
        # Private events don't expose full street address publicly.
        address = ""
        maps_url = ""
        ticket_price = ""
    else:
        venue = canonicalize_venue(raw.get("venue_name") or raw.get("title", ""))
        # Prefer canonical full address if we know it; otherwise keep whatever
        # Bandzoogle had.
        address = VENUE_FULL_ADDRESS.get(venue) or (raw.get("address_full") or "").strip()
        # Clean a trailing " TX" with no ZIP to " TX, USA"? Leave as-is — the
        # existing shows.json has mixed forms and the map URL works regardless.
        address_short = build_address_short(raw.get("city_state"), address)
        maps_url = build_maps_url(venue, address)
        # No ticket prices were displayed on any Bandzoogle past show — default
        # to "Free" to match the overwhelmingly dominant pattern in shows.json.
        # Ray can flip on review if any were actually paid.
        ticket_price = "Free"

    # Description strategy. First pass: sanitize out any prior-band-name
    # references (Jackson Crossing, Risky Business) — those were the same
    # members under earlier names; we present the archive under today's brand.
    raw_desc = raw.get("description_full") or ""
    raw_desc, _ = sanitize_prior_band_names(raw_desc)
    if should_regenerate_description(raw_desc):
        # Build a provisional show dict just for the generator to read.
        draft = generate_description_draft({
            "private": private,
            "venue": venue,
            "address_short": address_short,
            "ticket_price": ticket_price,
            "time": format_time(raw.get("time", "")),
            "day_name": day_name,
            "date": date_str,
        })
        description = draft  # May be "" for private events — that's fine.
    else:
        description = raw_desc.strip()

    entry = {
        "date": date_str,
        "day_name": day_name,
        "day_num": day_num,
        "month": month,
        "title": title if private else venue,
        "venue": venue,
        "address": address,
        "address_short": address_short,
        "time": format_time(raw.get("time", "")),
        "maps_url": maps_url,
        "private": private,
        "ticket_price": ticket_price,
        "description": description,
        "past": True,
        "source": SOURCE_TAG,
    }
    return entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Print merged JSON to stdout, do not write shows.json")
    args = parser.parse_args()

    raw_entries = json.loads(RAW.read_text())
    existing = json.loads(SHOWS.read_text())
    existing_dates = {s["date"] for s in existing}

    imported = []
    skipped_dedupe = []
    for raw in raw_entries:
        if raw["date"] in existing_dates:
            skipped_dedupe.append(raw["date"])
            continue
        imported.append(import_entry(raw))

    merged = existing + imported
    merged.sort(key=lambda s: s["date"])

    # Report
    print(f"Existing shows.json: {len(existing)} entries")
    print(f"Bandzoogle raw:      {len(raw_entries)} entries")
    print(f"Imported:            {len(imported)} (past=True)")
    print(f"Skipped (dedupe):    {len(skipped_dedupe)} "
          f"{skipped_dedupe if skipped_dedupe else ''}")
    print(f"Merged total:        {len(merged)} entries")
    print()

    # Breakdown of draft vs verbatim
    drafts = [s for s in imported if (s.get("description") or "").startswith("[DRAFT")]
    verbatim = [s for s in imported
                if s.get("description")
                and not s.get("description", "").startswith("[DRAFT")
                and not s.get("private")]
    private_past = [s for s in imported if s.get("private")]
    print(f"Imported breakdown:")
    print(f"  verbatim descriptions: {len(verbatim)}")
    print(f"  [DRAFT] descriptions:  {len(drafts)}")
    print(f"  private (no desc):     {len(private_past)}")

    if args.dry_run:
        print("\n--- DRY RUN: merged shows.json (not written) ---")
        print(json.dumps(merged, indent=2))
        return

    # Write with backup
    bak = SHOWS.with_suffix(".json.bak")
    shutil.copy2(SHOWS, bak)
    SHOWS.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"\n✓ shows.json updated ({bak.name} saved as backup)")


if __name__ == "__main__":
    main()
