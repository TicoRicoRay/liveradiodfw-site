#!/usr/bin/env python3
"""One-time historic calendar fetch: 2021-04-01 through 2024-08-08.

Pulls raw events from the band Google Calendar via webhook, runs them
through the existing is_gig_event() filter from sync_calendar.py, and
saves both raw and filtered sets to JSON for review.

Time window chosen:
  - start: 2021-04-01 (user request)
  - end:   2024-08-08 (one day before our earliest imported show, 2024-08-09)

Webhook has a TTL-less Apps Script that accepts arbitrary start/end
ISO dates and returns event objects with title/start/end/location/description.
"""
import json
import sys
from datetime import date
from pathlib import Path

# Reuse sync_calendar helpers
sys.path.insert(0, str(Path(__file__).parent))
from sync_calendar import is_gig_event, WEBHOOK_URL, PASSPHRASE

import requests

START = "2021-04-01"
END = "2024-08-08"

OUT_RAW = Path(__file__).parent / "calendar_historic_raw.json"
OUT_GIGS = Path(__file__).parent / "calendar_historic_gigs.json"
OUT_SKIP = Path(__file__).parent / "calendar_historic_skipped.json"

def fetch_range(start, end):
    payload = {
        "passphrase": PASSPHRASE,
        "action": "list",
        "start": start,
        "end": end,
    }
    resp = requests.post(WEBHOOK_URL, json=payload, allow_redirects=True, timeout=60)
    data = json.loads(resp.text)
    if data.get("status") != "ok":
        raise RuntimeError(f"Webhook error: {data}")
    return data["events"]

def main():
    print(f"Fetching calendar events {START} → {END}...")
    events = fetch_range(START, END)
    print(f"  raw events returned: {len(events)}")

    OUT_RAW.write_text(json.dumps(events, indent=2))
    print(f"  wrote {OUT_RAW.name} ({len(events)} events)")

    gigs = []
    skipped = []
    for e in events:
        try:
            if is_gig_event(e):
                gigs.append(e)
            else:
                skipped.append(e)
        except Exception as exc:
            # log parse failures as skipped
            e["_filter_error"] = str(exc)
            skipped.append(e)

    OUT_GIGS.write_text(json.dumps(gigs, indent=2))
    OUT_SKIP.write_text(json.dumps(skipped, indent=2))
    print(f"  gigs: {len(gigs)}, skipped: {len(skipped)}")
    print()
    print("=== GIGS (sorted by date) ===")
    for g in sorted(gigs, key=lambda x: x.get("start", "")):
        start = g.get("start", "?")[:10]
        title = g.get("title", "?")[:50]
        loc = g.get("location", "")[:60]
        print(f"  {start}  {title:<50}  @  {loc}")

if __name__ == "__main__":
    main()
