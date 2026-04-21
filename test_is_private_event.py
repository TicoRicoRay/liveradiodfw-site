"""Test harness for B8 fix. Validates is_private_event matches the
intended title patterns and rejects false positives.

Run from repo root:
    python3 test_is_private_event.py
"""
import sys
from sync_lib import is_private_event

CASES = [
    # (title, expected, why)
    # --- must match (private) ---
    ("LR - Test Event (Private)",          True,  "B8 original bug: parenthesized (Private)"),
    ("LR - Johnson Wedding - private",     True,  "trailing -private"),
    ("LR - Private BBQ",                   True,  "Private + unrelated noun"),
    ("LR - Private Party at Sue's",        True,  "pre-existing match, still passes"),
    ("LR - Private Event",                 True,  "pre-existing match, still passes"),
    ("LR - [PRIVATE] Corporate Xmas",      True,  "bracketed [PRIVATE]"),
    ("LR - Bartlett Gathering",            True,  "'gathering' keyword retained"),
    ("LR - Gatherings at the Venue",       True,  "Gatherings(r) venue, also private"),
    ("LR - private rehearsal",             True,  "lowercase, word-level"),
    ("LR - Holiday PRIVATE EVENT",         True,  "all-caps variant"),

    # --- must NOT match (public) ---
    ("LR - FRESH by Brookshire's",         False, "public venue"),
    ("LR - O G Cellars - 80s Dance Party", False, "party alone is not private"),
    ("LR - Frisco Rail Yard",              False, "public venue"),
    ("LR - Privateer Rodeo",               False, "'privateer' is not 'private' (word boundary)"),
    ("LR - Corporation Private Equity",    True,  "edge: 'private' as standalone word IS present -> privacy-safe default"),
    ("LR - Sweetwater Grill",              False, "public venue"),
    ("",                                   False, "empty title"),
    ("LR - ",                              False, "stripped title only"),
]


def main():
    failures = []
    for title, expected, why in CASES:
        actual = is_private_event(title)
        status = "OK " if actual == expected else "FAIL"
        print(f"{status}  expected={expected:<5}  actual={actual:<5}  {title!r}   ({why})")
        if actual != expected:
            failures.append((title, expected, actual, why))

    print()
    if failures:
        print(f"FAILED: {len(failures)}/{len(CASES)}")
        sys.exit(1)
    else:
        print(f"PASSED: {len(CASES)}/{len(CASES)}")


if __name__ == "__main__":
    main()
