"""Test harness for B15: cancelled/rescheduled show filtering.

Convention: Ray keeps the original GCal event as an audit record by renaming
it with a parenthetical suffix — "(Rescheduled ...)" or "(Cancelled)" —
instead of deleting it. The sync must filter those out of shows.json.

Run from repo root:
    python3 test_cancellation_reschedule.py
"""
import sys
from sync_calendar import is_gig_event


def ev(title, start="2026-04-19T00:15:00.000Z", end="2026-04-19T02:45:00.000Z",
       location="O G Cellars, 704 Co Rd 1895, Sunset, TX 76270, USA"):
    return {"title": title, "start": start, "end": end, "location": location}


CASES = [
    # (event, expected is_gig, why)

    # --- must be FILTERED OUT (cancelled / rescheduled audit records) ---
    (ev("OG Cellars - 80s Dance Party (Rescheduled due to Weather)"),
        False, "B15 live case: rescheduled suffix"),
    (ev("OG Cellars - 80s Dance Party (Rescheduled)"),
        False, "bare (Rescheduled) suffix"),
    (ev("OG Cellars - 80s Dance Party (RESCHEDULED DUE TO WEATHER)"),
        False, "case-insensitive rescheduled"),
    (ev("OG Cellars - 80s Dance Party (Cancelled)"),
        False, "British spelling cancelled"),
    (ev("OG Cellars - 80s Dance Party (Canceled)"),
        False, "American spelling canceled"),
    (ev("LR - Sweetwater Grill (Cancelled - venue closed)"),
        False, "LR prefix still filtered when cancelled"),
    (ev("Fresh by Brookshires (Rescheduled to Aug)"),
        False, "known venue still filtered when rescheduled"),

    # --- must still be GIGS (unchanged behavior) ---
    (ev("OG Cellars - 80s Dance Party",
        start="2026-08-02T01:00:00.000Z", end="2026-08-02T03:30:00.000Z"),
        True,  "B15 live case: new Aug 1 event unchanged"),
    (ev("LR - Sweetwater Grill",
        start="2026-06-14T01:30:00.000Z", end="2026-06-14T04:00:00.000Z"),
        True,  "normal LR prefix gig"),
    (ev("Fresh by Brookshires",
        start="2026-04-25T23:00:00.000Z", end="2026-04-26T01:30:00.000Z"),
        True,  "known venue, normal gig"),

    # --- no false positives on substring-like words ---
    (ev("LR - Grand Canceltown Fest",
        start="2026-05-10T00:30:00.000Z", end="2026-05-10T03:00:00.000Z"),
        True,  "'Canceltown' is not 'cancelled' — no paren, not end-anchored"),
    (ev("LR - The Rescheduling Ceremony",
        start="2026-05-10T00:30:00.000Z", end="2026-05-10T03:00:00.000Z"),
        True,  "'Rescheduling' without parens is not a filter match"),
    (ev("LR - Sweetwater (Special Event)",
        start="2026-06-14T01:30:00.000Z", end="2026-06-14T04:00:00.000Z"),
        True,  "non-cancellation parenthetical is fine"),
]


def main():
    failures = []
    for event, expected, why in CASES:
        actual = is_gig_event(event)
        status = "OK  " if actual == expected else "FAIL"
        print(f"{status}  expected={str(expected):<5}  actual={str(actual):<5}  {event['title']!r}   ({why})")
        if actual != expected:
            failures.append((event["title"], expected, actual, why))

    print()
    if failures:
        print(f"FAILED: {len(failures)}/{len(CASES)}")
        sys.exit(1)
    else:
        print(f"PASSED: {len(CASES)}/{len(CASES)}")


if __name__ == "__main__":
    main()
