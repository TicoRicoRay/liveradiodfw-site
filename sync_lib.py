#!/usr/bin/env python3
"""
sync_lib.py -- Pure library functions for the LiveRadioDFW calendar sync.
========================================================================

This module is the SAFE-TO-PUBLISH half of the calendar-sync code.  It
contains only pure functions and public constants -- **no webhook URL,
no passphrase, no network calls, no git operations, no email sending**.

It lives on the `gh-pages` branch so the live site's test files and
historic-import scripts can keep importing it:

    from sync_lib import is_private_event, is_gig_event, ...

The orchestration layer that *does* hold secrets -- fetching the
calendar over HTTPS, writing shows.json, invoking build scripts,
committing to git, sending alert emails -- lives in `sync_runner.py`
on Ray's Windows box, outside the repo.

History: extracted from the former `sync_calendar.py` during B7 Part 2
(2026-04-21) to eliminate the public exposure of the webhook
passphrase at https://www.liveradiodfw.com/sync_calendar.py.
"""

import re
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

# -- Shared constants (safe to publish) ---------------------------------------

CENTRAL_TZ = ZoneInfo("America/Chicago")

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
    r"\bplaying in\b",      # "Don playing in FW" -- other band gig
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


# -- Gig detection ------------------------------------------------------------

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
# raw title -- including parenthesized (Private) and bracketed [PRIVATE]
# -- is available at privacy-decision time.
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


# -- Ticket-price parsing -----------------------------------------------------

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


# -- Description draft generation (B16 Stage 1) -------------------------------

def generate_description_draft(show):
    """Compose a 3-5 sentence machine-generated description draft from the
    calendar-owned fields of a show dict. B16 Stage 1: the draft is proposed
    to Ray via the alert email; nothing auto-publishes.

    Voice calibration is based on the 7 existing hand-curated descriptions
    as of 2026-04-18:
      - Opener rotation: "Live Radio DFW <verb> <venue> in <city>" or
        "Catch Live Radio DFW at <venue> in <city>"
      - 3-5 sentences, ~300-500 chars
      - Mentions ticket language (Free / no cover / $N admission)
      - Geographic call-out (city + a nearby community or region)
      - No em-dashes, no exclamation points, present tense

    Deterministic: same show dict -> same draft (no LLM, no RNG). The opener
    is chosen by hashing the date+venue so we don't get "Live Radio DFW
    takes over ..." on every single new page.

    Returns the draft string, or "" if the show is private or has insufficient
    information (no venue, TBA time, etc.) to make a reasonable draft.
    """
    if show.get("private"):
        return ""
    venue = show.get("venue", "").strip()
    city = show.get("address_short", "").strip()
    if not venue or not city or city == "DFW Area":
        return ""
    ticket = show.get("ticket_price", "")
    day_name = show.get("day_name", "")
    date_str = show.get("date", "")

    # Rotate opener based on a stable hash of (date, venue) so repeat bookings
    # at the same venue don't all get the same sentence.
    openers = [
        f"Live Radio DFW heads to {venue} in {city}",
        f"Catch Live Radio DFW at {venue} in {city}",
        f"Live Radio DFW takes the stage at {venue} in {city}",
        f"Live Radio DFW returns to {venue} in {city}",
    ]
    # Stable hash across processes (Python's built-in hash() is randomized
    # per-process via PYTHONHASHSEED; we need the same draft every run).
    key = hashlib.sha256(f"{date_str}|{venue}".encode()).digest()
    opener = openers[key[0] % len(openers)]

    # Day-of-week framing for the opener sentence
    day_full = {
        "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday",
        "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday",
    }.get(day_name, "")
    if day_full:
        opener_sentence = f"{opener} for a {day_full} evening of live music."
    else:
        opener_sentence = f"{opener} for an evening of live music."

    # Ticket sentence
    if ticket == "Free":
        ticket_sentence = "No cover charge, no tickets needed."
    elif ticket and ticket != TICKET_PRICE_MISSING:
        ticket_sentence = f"Admission is {ticket}."
    else:
        ticket_sentence = ""

    # Generic middle sentence about the show itself (intentionally bland so
    # Ray knows it needs venue-specific enrichment before ship).
    middle_sentence = (
        "We'll be playing our mix of 70s, 80s, classic rock, and oldies covers "
        "across the set."
    )

    # Close with a geographic hint if we can infer one from the city string.
    close_sentence = (
        f"A solid night out for the {city} crowd and the surrounding DFW Metroplex communities."
    )

    # Flag the draft so humans never mistake it for finished copy.
    flag = (
        "[DRAFT - machine-generated from calendar fields; "
        "review and enrich with venue-specific details before publish.]"
    )

    parts = [opener_sentence, middle_sentence]
    if ticket_sentence:
        parts.append(ticket_sentence)
    parts.append(close_sentence)
    body = " ".join(parts)
    return f"{flag} {body}"


# -- Approval workflow (B32 / R25 Part A) -------------------------------------

def approval_token(show, draft):
    """Return a stable 12-char token identifying a specific (show, draft)
    pair for the reply-to-approve workflow.

    Token is sha256(show_date | venue | draft)[:12], lowercased hex. Same
    inputs -> same token across processes, machines, and runs, so the daily
    sync can re-generate the same token tomorrow if the same draft still
    applies. If the draft text changes (because we tweaked the generator),
    the token changes too, which correctly invalidates any stale pending
    approval for the old text.

    Inputs:
      show  -- a shows.json-shaped dict; uses show['date'] and show['venue']
      draft -- the exact draft string that will appear in the email body

    Returns 12-char hex string. Never empty (empty inputs still hash).
    """
    date_str = show.get("date", "") if show else ""
    venue = show.get("venue", "") if show else ""
    payload = f"{date_str}|{venue}|{draft}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def build_approval_email_section(show, draft, alert_email):
    """Render the MISSING-INFO email block for a single show that is missing
    its About-this-show description. Includes the proposed draft plus two
    mailto links so Ray can reply-to-approve or reply-to-edit without
    leaving his mail client (B32 / R25 Part A).

    The output is plain text. EmailMessage.set_content() sends text/plain,
    and every mainstream mail client (Gmail, Apple Mail, Outlook on iOS and
    desktop) auto-linkifies bare mailto: URLs, so no HTML is required.

    Token is in the SUBJECT line, not the address, so we do not depend on
    the mail host supporting plus-subaddressing. Part B's
    process_approvals.py parses the subject.

    Inputs:
      show        -- shows.json-shaped dict
      draft       -- non-empty draft string (caller must pre-check)
      alert_email -- the ALERT_EMAIL value from sync_runner (where replies go)

    Returns a plain-text block ready to concatenate into the email body.
    """
    token = approval_token(show, draft)
    title = show.get("title", show.get("venue", "Unknown show"))
    show_date = show.get("date", "")

    # URL-encode the subject lines manually to keep the stdlib import
    # footprint of sync_lib small and dependency-free. We only need to
    # escape space -> %20 because the rest of the subject is ASCII
    # alphanumerics, hyphens, and the token.
    subj_approve = f"APPROVE%20{token}"
    subj_edit = f"EDIT%20{token}"

    # Body pre-fill for the EDIT reply: quoted draft so Ray can edit in
    # place and send. body= space encoding: %20 for spaces, %0A for newlines.
    edit_body_lines = [
        f"Editing description for {title} on {show_date}.",
        "Replace the text below with the final copy, keep the token line,",
        "then send. Everything after the token line is the new description.",
        "",
        f"TOKEN: {token}",
        "",
        draft,
    ]
    edit_body = "%0A".join(
        line.replace(" ", "%20").replace("\"", "%22")
        for line in edit_body_lines
    )

    mailto_approve = (
        f"mailto:{alert_email}?subject={subj_approve}"
    )
    mailto_edit = (
        f"mailto:{alert_email}?subject={subj_edit}&body={edit_body}"
    )

    block = (
        f"MISSING INFO:\n"
        f"  {title} on {show_date}\n"
        f"    Missing: About-this-show description\n"
        f"\n"
        f"  Proposed description draft (review before approving):\n"
        f"    {draft}\n"
        f"\n"
        f"  To approve this draft as-is, reply from this mailbox using:\n"
        f"    {mailto_approve}\n"
        f"\n"
        f"  To edit first, reply using (pre-fills draft in the body):\n"
        f"    {mailto_edit}\n"
        f"\n"
        f"  Approval token: {token}\n"
        f"  (Part B automation will consume this token; until then,\n"
        f"   Jarvis processes approvals manually in-session.)"
    )
    return block


# -- Event -> show conversion --------------------------------------------------

def calendar_event_to_show(event):
    """Convert a calendar event to a shows.json entry."""
    start_utc = datetime.fromisoformat(event["start"].replace("Z", "+00:00"))
    local_start = start_utc.astimezone(CENTRAL_TZ)

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
        # "Venue Name, 123 Street, City, ST 12345, USA" -- the venue name is already
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
        # Look for TX -- could be its own comma-separated part ("Allen, TX")
        # or embedded ("Sanger TX 76266")
        address_short = ""
        for i, p in enumerate(parts):
            p_stripped = p.strip()
            # Case 1: Part is just "TX" or "TX 7xxxx" -- city is the previous part.
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
            # Case 2: "Sanger TX 76266" -- TX embedded in the part with a city name.
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


# -- Missing-info detection ---------------------------------------------------

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
    # B16 Stage 1: flag missing description on public shows. The draft itself
    # is surfaced in the alert email body rather than returned here so the
    # normal MISSING INFO formatter stays single-purpose.
    if not show.get("private") and not show.get("description", "").strip():
        missing.append(
            "About-this-show description (hand-curated prose for SEO + the "
            "on-page About block; a machine-generated draft is included below "
            "for review/edit)"
        )
    return missing


# -- Merge helpers ------------------------------------------------------------

def detail_diffs(old_show, new_show):
    """Compare two show dicts across calendar-owned fields only.
    Returns list of (field, old_val, new_val) tuples.
    Hand-curated fields (anything outside CALENDAR_OWNED_FIELDS) are
    intentionally ignored -- they can't drift out of sync because the
    sync never touches them.
    """
    diffs = []
    for field in CALENDAR_OWNED_FIELDS:
        old_val = old_show.get(field, "")
        new_val = new_show.get(field, "")
        if str(old_val) != str(new_val):
            diffs.append((field, old_val, new_val))
    return diffs


def merge_calendar_fields(existing, fresh):
    """Return a copy of `existing` with only CALENDAR_OWNED_FIELDS overwritten
    by values from `fresh`. Preserves every other key on `existing`
    (descriptions, flyer paths, or any future hand-curated fields).
    """
    merged = dict(existing)  # start with EVERYTHING the user/site has
    for field in CALENDAR_OWNED_FIELDS:
        if field in fresh:
            merged[field] = fresh[field]
    return merged


# -- Back-compat shims --------------------------------------------------------
# The original sync_calendar.py exposed these as underscore-prefixed helpers;
# keep aliases so nothing existing breaks if it was reaching for them.
_detail_diffs = detail_diffs
_merge_calendar_fields = merge_calendar_fields
