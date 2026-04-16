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
  5. Runs build_shows.py to regenerate HTML
  6. Commits and pushes to GitHub if changes were made

Designed to run as a daily cron job.
Calendar is the source of truth — all changes flow from calendar to website.

GIG DETECTION RULES:
  - "LR -" prefix = confirmed LiveRadioDFW gig → auto-add to website
  - Known venue names (from shows.json history) → auto-add
  - "Private Party" / "Private Event" → auto-add as private
  - Everything else (rehearsals, personal, other bands, holds) → skip
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
PASSPHRASE = "El3QSCjanehlVwDpTOO_TBS-JGC9v7nW"
BASE = Path(__file__).parent
ALERT_EMAIL = "info@liveradiodfw.com"
CDT = ZoneInfo("America/Chicago")

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
]

# Known venue names that are definitely LR gigs (built from history)
KNOWN_VENUES = [
    "og cellars", "fresh by brookshires", "frisco rail yard",
    "watters creek", "sweetwater grill", "uptown rail",
    "the gathering", "3 nations",
]

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


def is_private_event(title):
    """Check if event title indicates a private event."""
    t = title.lower()
    return "private party" in t or "private event" in t or "gathering" in t


def parse_ticket_price(description):
    """Extract ticket price from event description.
    Looks for patterns like:
      Tickets: $25
      Ticket Price: $15
      Tickets: Free
      Ticket: $10
    Returns the matched string (e.g. '$25', 'Free') or 'Free' if not found.
    """
    if not description:
        return "Free"
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
    return "Free"


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

        # Build short address (city, state)
        # Look for TX — could be its own comma-separated part ("Allen, TX")
        # or embedded ("Sanger TX 76266")
        address_short = ""
        for i, p in enumerate(parts):
            p_stripped = p.strip()
            # Case 1: Part is just "TX" or "TX 7xxxx" — city is the previous part
            if re.match(r'^TX\b', p_stripped, re.IGNORECASE):
                if i > 0:
                    city = parts[i-1].strip()
                    if re.match(r'^\d', city):
                        city = parts[max(0, i-2)].strip()
                    address_short = f"{city}, TX"
                else:
                    address_short = p_stripped
                break
            # Case 2: "Sanger TX 76266" — TX embedded in the part with a city name
            tx_match = re.search(r'(\S+)\s+TX\b', p_stripped, re.IGNORECASE)
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

    # Parse ticket price from description
    ticket_price = parse_ticket_price(event.get("description", ""))

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
    subprocess.run(["git", "add", "shows.json", "shows.html", "index.html"],
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
    """Compare two show dicts and return list of (field, old_val, new_val) tuples."""
    diffs = []
    for field in ["time", "venue", "address", "address_short", "title", "maps_url", "private", "ticket_price"]:
        old_val = old_show.get(field, "")
        new_val = new_show.get(field, "")
        if str(old_val) != str(new_val):
            diffs.append((field, old_val, new_val))
    return diffs


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
    updates = []       # list of (old_show, new_show, diffs)
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
            # Existing show — check for detail changes
            old_show = current_by_date[show["date"]]
            diffs = _detail_diffs(old_show, show)
            if diffs:
                updates.append((old_show, show, diffs))
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

    # 6c. Updates (overwrite old show with new calendar data)
    if updates:
        for old_show, new_show, diffs in updates:
            for i, s in enumerate(current_shows):
                if s["date"] == new_show["date"]:
                    current_shows[i] = new_show
                    break
            changed_fields = ", ".join(f[0] for f in diffs)
            commit_parts.append(f"Updated {new_show['title']} ({new_show['date']}): {changed_fields}")

    if adds or removals or updates:
        current_shows.sort(key=lambda s: s["date"])
        with open(BASE / "shows.json", "w") as f:
            json.dump(current_shows, f, indent=2)
            f.write("\n")
        subprocess.run([sys.executable, str(BASE / "build_shows.py")], check=True)
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
            "Calendar is the source of truth — all changes flow automatically.\n"
            "If anything looks wrong, update the calendar and it will\n"
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
