#!/usr/bin/env python3
"""
sync_calendar.py — Daily Calendar ↔ Website Sync for LiveRadioDFW
==================================================================
Pulls events from the band's Google Calendar via webhook,
compares against shows.json, and:
  1. Adds new confirmed gig events to shows.json
  2. Auto-REMOVES shows deleted from calendar + emails info@ to confirm
  3. Auto-UPDATES changed details (time, location, title) + emails info@
  4. Emails info@liveradiodfw.com if required info is missing
  5. Runs build_shows.py to regenerate show HTML
  5b. Runs build_show_pages.py to regenerate individual show pages
  5c. Runs build_includes.py to stamp nav/footer into all pages
  6. Commits and pushes to GitHub if changes were made

Designed to run as a daily cron job.
Calendar is the source of truth — FOR CALENDAR-OWNED FIELDS ONLY.

⚠️  NON-DESTRUCTIVE SYNC (updated 2026-04-17):
  Calendar owns ONLY the fields listed in CALENDAR_OWNED_FIELDS below.
  Any other field on a show entry (e.g. "description", future hand-curated
  fields) is PRESERVED by the sync. When updating an existing show we
  merge calendar-owned fields over the existing entry instead of replacing
  the whole dict. This prevents the sync from silently wiping hand-written
  copy on every run.

GIG DETECTION RULES:
  - "LR -" prefix = confirmed LiveRadioDFW gig → auto-add to website
  - Known venue names (from shows.json history) → auto-add
  - "Private Party" / "Private Event" → auto-add as private
  - Everything else (rehearsals, personal, other bands, holds) → skip

CANCELLATION / RESCHEDULE CONVENTION (added 2026-04-18, B15):
  When a show is cancelled or rescheduled, DO NOT delete the original
  Google Calendar event. Instead:
    1. Rename the original event with a parenthetical suffix at the end:
         "<original title> (Rescheduled due to Weather)"
         "<original title> (Cancelled)"
    2. If rescheduled, create a brand-new event for the new date
       (the sync will pick it up via the normal KNOWN_VENUES / "LR -" path).
  The renamed original stays on the calendar as a band-facing audit record
  of what happened, but is filtered out of shows.json so the public site
  never sends fans to a dead show. See SKIP_PATTERNS below.
"""

import json
import subprocess
import sys
import re
import asyncio
from datetime import datetime, date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# ── Config ────────────────────────────────────────────────────────────────────
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbz9nOyNo-_YOeU0x4rnq76Y5iuxyiZOSUES2m7Lye4TmXZ6wyQNG9cUp7r9ithYTlbLeA/exec"
PASSPHRASE = "L7D3U7cLUHDcjHSpPjVsomp5LqufSFHj"
BASE = Path(__file__).parent
ALERT_EMAIL = "info@liveradiodfw.com"
CDT = ZoneInfo("America/Chicago")

# Fields that are populated from the Google Calendar event.
# These are the ONLY fields the sync is allowed to overwrite on existing shows.
# Anything else on a show dict (e.g. "description") is hand-curated and must
# be preserved across sync runs.
CALENDAR_OWNED_FIELDS = [
    "date",
    "day_name",
    "day_num",
    "month",
    "title",
    "venue",
    "address",
    "address_short",
    "time",
    "maps_url",
    "private",
    "ticket_price",
]

# Events with these patterns in the title are NEVER gigs
SKIP_PATTERNS = [
    r"^rehearsal$",
    r"\bout\b",             # "Kyle out", "Donna OUT", "Ray Out", "Don Out"
    r"\bvacation\b",
    r"\bbirthday\b",
    r"\banniversary\b",
    r"\bholiday\b",
    r"\bblock\b",           # "Block Kyle Out"
    r"\bhold\b",            # "Hold til..."
    r"\bpractice\b",
    r"\bstudio\b",
    r"\brecording\b",
    r"\bmeeting\b",
    r"\bquote expires\b",
    r"\blead!\b",
    r"\bplaying in\b",      # "Don playing in FW" — other band gig
    r"\bin\s+(atlanta|detroit|london|lv|boston|costa rica)\b",  # travel
    r"\bchasing\b",         # "Ray Chasing Tornadoes"
    r"\bcamp\b",            # "Dude Rock Camp"
    r"\bbeach\b",           # "Panama Beach Vacation"
    r"to-jo",               # Kyle's other band
    r"live wire",           # Don's other band
    r"fat daddy",           # Kyle's other band venue
    # Cancellation / reschedule convention (B15, 2026-04-18):
    # Ray renames an event with a parenthetical suffix at the end of the
    # title when a show is cancelled or rescheduled. The original stays on
    # GCal for audit, but must be filtered out of the public shows.json.
    r"\(.*\brescheduled\b.*\)\s*$",   # "... (Rescheduled due to Weather)"
    r"\(.*\bcancel(?:l)?ed\b.*\)\s*$",  # "... (Cancelled)" / "(Canceled)"
]

# Known venue names that are definitely LR gigs (built from history)
KNOWN_VENUES = [
    "og cellars", "fresh by brookshires", "frisco rail yard",
    "watters creek", "sweetwater grill", "uptown rail",
    "the gathering", "3 nations",
]

# Sentinel value returned by parse_ticket_price when no price is found.
# We default to "" (blank) instead of "Free" so the website shows no price
# rather than a potentially wrong one. The missing-info pathway notifies
# info@liveradiodfw.com so a human can add "Tickets: $XX" to the calendar.
TICKET_PRICE_MISSING = ""

# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_calendar_events():
    """Pull all future events from the band's Google Calendar via webhook."""
    import requests
    today = date.today()
    end_date = today + timedelta(days=365)
    payload = {
        "passphrase": PASSPHRASE,
        "action": "list",
        "start": today.isoformat(),
        "end": end_date.isoformat()
    }
    resp = requests.post(WEBHOOK_URL, json=payload, allow_redirects=True)
    data = json.loads(resp.text)
    if data.get("status") != "ok":
        raise RuntimeError(f"Webhook error: {data}")
    return data["events"]


def is_gig_event(event):
    """Determine if a calendar event is a confirmed LiveRadioDFW gig."""
    title = event.get("title", "").strip()
    title_lower = title.lower()

    # Rule 1: Skip anything matching known non-gig patterns
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, title_lower):
            return False

    # Rule 2: All-day events (24+ hours) are never gigs
    start = datetime.fromisoformat(event["start"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(event["end"].replace("Z", "+00:00"))
    duration_hours = (end - start).total_seconds() / 3600
    if duration_hours >= 24:
        return False

    # Rule 3: "LR -" prefix = confirmed gig
    if title_lower.startswith("lr -") or title_lower.startswith("lr-"):
        return True

    # Rule 4: "Private Party" or "Private Event" = gig
    if "private party" in title_lower or "private event" in title_lower:
        return True

    # Rule 5: Known venue name match = gig
    for venue in KNOWN_VENUES:
        if venue in title_lower:
            return True

    # Rule 6: Location at known venue
    location_lower = event.get("location", "").lower()
    for venue in KNOWN_VENUES:
        if venue in location_lower:
            return True

    # Default: NOT a gig. Better to miss one and have a human add it
    # than to auto-publish something that shouldn't be on the website.
    return False


# B8: match 'private' as a standalone word anywhere in the title.
# The word boundary \b prevents false matches on substrings like
# 'privateer' or 'privatize'. Matching is case-insensitive.
# Also retain 'gathering' / 'gatherings' as an explicit trigger for the
# Gatherings(r) venue family, which is always private.
# The function is deliberately called with the RAW calendar title
# (before the 'LR -' prefix strip) so any disambiguating context in the
# raw title — including parenthesized (Private) and bracketed [PRIVATE]
# — is available at privacy-decision time. See sync_calendar.py line 213.
_PRIVATE_WORD_RE = re.compile(r"\bprivate\b", re.IGNORECASE)
_GATHERING_WORD_RE = re.compile(r"\bgatherings?\b", re.IGNORECASE)

def is_private_event(title):
    """Return True when the event title indicates a private booking.

    Matches:
      - the standalone word 'private' anywhere in the title, including
        '(Private)', '[PRIVATE]', '- private', 'Private BBQ', etc.
      - the word 'gathering' / 'gatherings' (the Gatherings(r) venue family).

    Does NOT match:
      - substrings like 'privateer' or 'privatize' (word boundary required).
      - the word 'party' alone (would over-match '80s Dance Party' etc.).
    """
    if not title:
        return False
    return bool(_PRIVATE_WORD_RE.search(title) or _GATHERING_WORD_RE.search(title))


def parse_ticket_price(description):
    """Extract ticket price from event description.
    Looks for patterns like:
      Tickets: $25
      Ticket Price: $15
      Tickets: Free
      Ticket: $10
    Returns the matched string (e.g. '$25', 'Free') OR TICKET_PRICE_MISSING ('')
    if no price directive is found in the description. Callers can treat
    TICKET_PRICE_MISSING as "needs human attention" and surface an alert.
    """
    if not description:
        return TICKET_PRICE_MISSING
    # Match "Tickets:", "Ticket Price:", "Ticket:" followed by a price or "Free"
    match = re.search(
        r'tickets?(?:\s*price)?\s*:\s*(\$[\d,.]+|free)',
        description,
        re.IGNORECASE
    )
    if match:
        val = match.group(1).strip()
        if val.lower() == "free":
            return "Free"
        return val
    return TICKET_PRICE_MISSING


def calendar_event_to_show(event):
    """Convert a calendar event to a shows.json entry."""
    start_utc = datetime.fromisoformat(event["start"].replace("Z", "+00:00"))
    end_utc = datetime.fromisoformat(event["end"].replace("Z", "+00:00"))
    local_start = start_utc.astimezone(CDT)
    local_end = end_utc.astimezone(CDT)

    # Title: strip "LR - " prefix
    raw_title = event.get("title", "").strip()
    title = re.sub(r'^LR\s*-\s*', '', raw_title, flags=re.IGNORECASE).strip()

    private = is_private_event(raw_title)

    # Format time
    if local_start.hour == 0 and local_start.minute == 0:
        time_str = "TBA"
    else:
        h = local_start.hour
        m = local_start.minute
        am_pm = "AM" if h < 12 else "PM"
        dh = h if h <= 12 else h - 12
        if dh == 0:
            dh = 12
        time_str = f"{dh}:{m:02d} {am_pm}"

    # Parse location
    location = event.get("location", "").strip()
    # Clean up Google's newline formatting
    location = location.replace("\n", ", ")

    if location:
        parts = [p.strip() for p in location.split(",")]
        venue = parts[0]
        address = location

        # B10 fix: Google's "location" field from Places is often populated as
        # "Venue Name, 123 Street, City, ST 12345, USA" — the venue name is already
        # the first segment. If we keep it duplicated in `address`, every downstream
        # consumer (/shows render, show-detail page, JSON-LD schema, Add-to-Calendar
        # button, generated .ics) ends up showing the venue name twice. Strip the
        # first segment from `address` when it looks like a venue name (starts with
        # a letter) AND the second segment looks like a street address (starts with
        # a digit). That keeps bare-street-address inputs like "1115 Vista Wy, ..."
        # intact for private-event parsing, but cleans up Google Places-formatted
        # entries like "FRESH by Brookshire's, 5100 I-30, Fate, TX 75189, USA".
        if (len(parts) >= 2
                and parts[0]
                and parts[0][0].isalpha()
                and parts[1]
                and parts[1][0].isdigit()):
            address = ", ".join(parts[1:]).strip()

        # Build short address (city, state)
        # Look for TX — could be its own comma-separated part ("Allen, TX")
        # or embedded ("Sanger TX 76266")
        address_short = ""
        for i, p in enumerate(parts):
            p_stripped = p.strip()
            # Case 1: Part is just "TX" or "TX 7xxxx" — city is the previous part.
            # Require TX to be followed by whitespace, end-of-string, or a digit (ZIP).
            # Do NOT match "TX-276" (a state highway designator); \b alone would match
            # at the X-hyphen boundary and misfire (B10 follow-up: Sweetwater Grill's
            # address "4884 TX-276, Royse City, TX 75189, USA" exposed this).
            if re.match(r'^TX(?=\s|$|\d)', p_stripped, re.IGNORECASE):
                if i > 0:
                    city = parts[i-1].strip()
                    if re.match(r'^\d', city):
                        city = parts[max(0, i-2)].strip()
                    address_short = f"{city}, TX"
                else:
                    address_short = p_stripped
                break
            # Case 2: "Sanger TX 76266" — TX embedded in the part with a city name.
            # Same lookahead guard as Case 1 so we don't capture "4884" out of
            # "4884 TX-276".
            tx_match = re.search(r'(\S+)\s+TX(?=\s|$|\d)', p_stripped, re.IGNORECASE)
            if tx_match:
                city = tx_match.group(1)
                address_short = f"{city}, TX"
                break
        if not address_short:
            address_short = ", ".join(parts[-2:]) if len(parts) >= 2 else location
    else:
        venue = title
        address = ""
        address_short = ""

    # Maps URL
    maps_url = ""
    if not private and location:
        maps_url = "https://maps.google.com/?q=" + location.replace(" ", "+").replace(",", "%2C")

    if private:
        title = "Private Event"
        venue = "Private Event"
        # For private events, show only city/state for public display.
        # If we couldn't parse a "City, TX" from the address, use "DFW Area"
        # to avoid leaking full venue names or street addresses.
        if address_short and not re.search(r'\bTX\b', address_short, re.IGNORECASE):
            address_short = "DFW Area"

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Parse ticket price from description (never show price on private events)
    ticket_price = "" if private else parse_ticket_price(event.get("description", ""))

    return {
        "date": local_start.strftime("%Y-%m-%d"),
        "day_name": day_names[local_start.weekday()],
        "day_num": str(local_start.day),
        "month": months[local_start.month - 1],
        "title": title,
        "venue": venue,
        "address": address,
        "address_short": address_short,
        "time": time_str,
        "maps_url": maps_url,
        "private": private,
        "ticket_price": ticket_price,
    }


def check_missing_info(show, event):
    """Check if a show entry is missing required information for the website."""
    missing = []
    if not event.get("location", "").strip():
        missing.append("Venue address/location")
    if show["time"] == "TBA":
        missing.append("Start time (calendar event has no specific time set)")
    # Ticket price is required on PUBLIC events. Private events intentionally
    # have no price displayed. TICKET_PRICE_MISSING ('') means the parser
    # couldn't find "Tickets: $XX" (or "Tickets: Free") in the description.
    if not show.get("private") and show.get("ticket_price", "") == TICKET_PRICE_MISSING:
        missing.append(
            "Ticket price (add a line like 'Tickets: $25' or 'Tickets: Free' "
            "to the calendar event description)"
        )
    return missing


async def send_alert_email(subject, body):
    """Send an alert email to info@liveradiodfw.com."""
    proc = await asyncio.create_subprocess_exec(
        "external-tool", "call", json.dumps({
            "source_id": "outlook",
            "tool_name": "send_email",
            "arguments": {
                "action": {
                    "action": "send",
                    "to": [ALERT_EMAIL],
                    "cc": [],
                    "bcc": [],
                    "subject": subject,
                    "body": body
                }
            }
        }),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        print(f"  WARNING: Failed to send email: {stderr.decode()}", file=sys.stderr)
        return False
    return True


def git_commit_and_push(message):
    """Commit changes and push to GitHub."""
    subprocess.run(["git", "add", "-A"],
                   cwd=BASE, check=True)

    result = subprocess.run(["git", "diff", "--cached", "--quiet"],
                            cwd=BASE, capture_output=True)
    if result.returncode == 0:
        print("No file changes to commit.")
        return False

    subprocess.run(["git", "commit", "-m", message], cwd=BASE, check=True)
    subprocess.run(["git", "push", "origin", "gh-pages"], cwd=BASE, check=True)
    print("Pushed to GitHub")
    return True


# ── Main Sync ─────────────────────────────────────────────────────────────────

def _detail_diffs(old_show, new_show):
    """Compare two show dicts across calendar-owned fields only.
    Returns list of (field, old_val, new_val) tuples.
    Hand-curated fields (anything outside CALENDAR_OWNED_FIELDS) are
    intentionally ignored — they can't drift out of sync because the
    sync never touches them.
    """
    diffs = []
    for field in CALENDAR_OWNED_FIELDS:
        old_val = old_show.get(field, "")
        new_val = new_show.get(field, "")
        if str(old_val) != str(new_val):
            diffs.append((field, old_val, new_val))
    return diffs


def _merge_calendar_fields(existing, fresh):
    """Return a copy of `existing` with only CALENDAR_OWNED_FIELDS overwritten
    by values from `fresh`. Preserves every other key on `existing`
    (descriptions, flyer paths, or any future hand-curated fields).
    """
    merged = dict(existing)  # start with EVERYTHING the user/site has
    for field in CALENDAR_OWNED_FIELDS:
        if field in fresh:
            merged[field] = fresh[field]
    return merged


async def main():
    print(f"=== LiveRadioDFW Calendar Sync — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    # 1. Load current shows.json
    with open(BASE / "shows.json") as f:
        current_shows = json.load(f)

    current_by_date = {s["date"]: s for s in current_shows}
    print(f"Current shows.json: {len(current_shows)} entries")

    # 2. Fetch calendar events
    cal_events = fetch_calendar_events()
    print(f"Calendar events fetched: {len(cal_events)} total")

    # 3. Filter to confirmed gigs
    gigs = [e for e in cal_events if is_gig_event(e)]
    print(f"Confirmed gigs: {len(gigs)}")
    for g in gigs:
        print(f"  - {g['title']}")

    # 4. Convert to show entries and compare
    adds = []
    updates = []       # list of (old_show, merged_show, diffs)
    missing_info = []

    cal_dates = set()  # track all calendar gig dates for deletion check

    for event in gigs:
        show = calendar_event_to_show(event)
        cal_dates.add(show["date"])

        # Check for missing required info
        missing = check_missing_info(show, event)
        if missing:
            missing_info.append((show, missing))

        if show["date"] not in current_by_date:
            # New show not on website
            adds.append(show)
            print(f"  + NEW: {show['title']} on {show['date']}")
        else:
            # Existing show — check for detail changes in calendar-owned fields.
            # Merge instead of replace so we don't wipe hand-curated fields.
            old_show = current_by_date[show["date"]]
            diffs = _detail_diffs(old_show, show)
            if diffs:
                merged = _merge_calendar_fields(old_show, show)
                updates.append((old_show, merged, diffs))
                print(f"  ~ UPDATED: {show['title']} on {show['date']}")
                for field, old_val, new_val in diffs:
                    print(f"      {field}: '{old_val}' → '{new_val}'")

    # 5. Check for shows on website that disappeared from calendar
    #    Calendar is source of truth → auto-remove + email info@ for safety
    removals = []  # list of show dicts removed
    for show in current_shows:
        show_date = datetime.strptime(show["date"], "%Y-%m-%d").date()
        if show_date >= date.today() and show["date"] not in cal_dates:
            removals.append(show)
            print(f"  ✕ REMOVED: {show['title']} on {show['date']} — not on calendar")

    # 6. Apply changes to shows.json
    changed = False
    commit_parts = []

    # 6a. Additions
    if adds:
        for show in adds:
            current_shows.append(show)
        commit_parts.extend(f"Added {s['title']} ({s['date']})" for s in adds)

    # 6b. Removals
    if removals:
        removal_dates = {s["date"] for s in removals}
        current_shows = [s for s in current_shows if s["date"] not in removal_dates]
        commit_parts.extend(f"Removed {s['title']} ({s['date']})" for s in removals)

    # 6c. Updates — merge calendar-owned fields into existing entry,
    #     preserving all hand-curated fields (description, etc.).
    if updates:
        for old_show, merged_show, diffs in updates:
            for i, s in enumerate(current_shows):
                if s["date"] == merged_show["date"]:
                    current_shows[i] = merged_show
                    break
            changed_fields = ", ".join(f[0] for f in diffs)
            commit_parts.append(f"Updated {merged_show['title']} ({merged_show['date']}): {changed_fields}")

    if adds or removals or updates:
        current_shows.sort(key=lambda s: s["date"])
        with open(BASE / "shows.json", "w") as f:
            json.dump(current_shows, f, indent=2)
            f.write("\n")
        subprocess.run([sys.executable, str(BASE / "build_shows.py")], check=True)
        subprocess.run([sys.executable, str(BASE / "build_show_pages.py")], check=True)
        subprocess.run([sys.executable, str(BASE / "build_includes.py")], check=True)
        commit_msg = "Auto-sync: " + "; ".join(commit_parts)
        changed = git_commit_and_push(commit_msg)

    # 7. Send alert emails
    email_parts = []

    if removals:
        for show in removals:
            email_parts.append(
                f"🗑 REMOVED from website:\n"
                f"  {show['title']} on {show['date']}\n"
                f"  This show was on the website but is no longer on the band calendar.\n"
                f"  It has been automatically removed from the website.\n"
                f"  If this was a mistake, re-add the event to the calendar and\n"
                f"  it will reappear on the website at the next daily sync (8 AM CDT)."
            )

    if updates:
        for old_show, new_show, diffs in updates:
            changes_text = "\n".join(
                f"    {field}: '{old_val}' → '{new_val}'"
                for field, old_val, new_val in diffs
            )
            email_parts.append(
                f"📝 UPDATED on website:\n"
                f"  {new_show['title']} on {new_show['date']}\n"
                f"  The following details changed on the calendar and have been\n"
                f"  automatically updated on the website:\n"
                f"{changes_text}"
            )

    if missing_info:
        for show, fields in missing_info:
            email_parts.append(
                f"⚠️ MISSING INFO:\n"
                f"  {show['title']} on {show['date']}\n"
                + "\n".join(f"    Missing: {f}" for f in fields)
            )

    if email_parts:
        body = (
            "Hey team,\n\n"
            "The daily calendar sync made the following changes:\n\n"
            + "\n\n".join(email_parts)
            + "\n\n"
            "Calendar is the source of truth for scheduling fields (time, venue,\n"
            "address, title, maps_url, private, ticket_price). All other fields on\n"
            "show pages (e.g. marketing descriptions) are hand-curated and are\n"
            "preserved across every sync.\n\n"
            "If anything above looks wrong, update the calendar and it will\n"
            "be corrected at the next sync (daily at 8 AM CDT).\n\n"
            "— Jarvis (LiveRadioDFW Calendar Sync)"
        )
        action_count = len(removals) + len(updates) + len(missing_info)
        subject = f"[LiveRadioDFW] Calendar sync — {action_count} change(s) applied"
        sent = await send_alert_email(subject, body)
        if sent:
            print(f"\nAlert email sent ({action_count} items)")

    # 8. Summary
    print(f"\n=== Summary ===")
    if adds:
        print(f"Added to website: {len(adds)}")
        for s in adds:
            print(f"  + {s['title']} on {s['date']}")
    if removals:
        print(f"Removed from website: {len(removals)}")
        for s in removals:
            print(f"  ✕ {s['title']} on {s['date']}")
    if updates:
        print(f"Updated on website: {len(updates)}")
        for old_s, new_s, diffs in updates:
            print(f"  ~ {new_s['title']} on {new_s['date']}")
    if missing_info:
        print(f"Missing info alerts: {len(missing_info)}")
    if not adds and not removals and not updates and not missing_info:
        print("Everything in sync. No issues found.")

    return adds, removals, updates, missing_info


if __name__ == "__main__":
    asyncio.run(main())
