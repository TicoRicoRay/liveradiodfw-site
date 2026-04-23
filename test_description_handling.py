"""Test harness for B16 Stage 1: description handling for new shows.

Covers:
  - generate_description_draft() voice + determinism + opt-outs
  - check_missing_info() flags missing description on public shows only

Run from repo root:
    python3 test_description_handling.py
"""
import sys
from sync_lib import (
    generate_description_draft,
    check_missing_info,
    approval_token,
    build_approval_email_section,
)


def public_show(**overrides):
    base = {
        "date": "2026-08-01",
        "day_name": "Sat",
        "day_num": "1",
        "month": "Aug",
        "title": "OG Cellars - 80s Dance Party",
        "venue": "O G Cellars",
        "address": "704 Co Rd 1895, Sunset, TX 76270, USA",
        "address_short": "Sunset, TX",
        "time": "8:00 PM",
        "maps_url": "https://maps.google.com/?q=...",
        "private": False,
        "ticket_price": "$25",
    }
    base.update(overrides)
    return base


# Event stub for check_missing_info (it only reads event.location)
def ev(location="O G Cellars, 704 Co Rd 1895, Sunset, TX 76270, USA"):
    return {"location": location}


failures = []


def check(label, cond, detail=""):
    status = "OK  " if cond else "FAIL"
    print(f"{status}  {label}" + (f"  -- {detail}" if detail else ""))
    if not cond:
        failures.append((label, detail))


print("=== generate_description_draft ===")

# 1. Produces non-empty draft for a well-formed public show
draft = generate_description_draft(public_show())
check("public show with full info produces a draft", bool(draft))
check("draft is flagged so it can never be mistaken for finished copy",
      draft.startswith("[DRAFT"), f"first 60 chars: {draft[:60]!r}")
check("draft mentions the venue name", "O G Cellars" in draft)
check("draft mentions the city", "Sunset, TX" in draft)
check("draft has no em-dash (cardinal rule)", "\u2014" not in draft and "--" not in draft)
check("draft has no exclamation points", "!" not in draft)
check("draft is roughly 300-600 chars", 250 <= len(draft) <= 700,
      f"actual len={len(draft)}")

# 2. Determinism across runs (stable hash, not PYTHONHASHSEED-dependent)
draft2 = generate_description_draft(public_show())
check("draft is deterministic (same input -> same output)", draft == draft2)

# 3. Opener rotation -- different (date, venue) picks different openers
drafts = set()
for d, v in [
    ("2026-08-01", "O G Cellars"),
    ("2026-08-15", "Frisco Rail Yard"),
    ("2026-09-12", "FRESH by Brookshire's"),
    ("2026-09-26", "Uptown Rail Brewery"),
]:
    dd = generate_description_draft(public_show(date=d, venue=v, address_short="Test, TX"))
    # Extract the opener (first sentence after the [DRAFT ...] flag)
    body = dd.split("] ", 1)[1] if "] " in dd else dd
    opener = body.split(".")[0]
    drafts.add(opener.split(" at ")[0].split(" to ")[0].split(" the stage")[0])
check("opener rotation produces at least 2 distinct openers across 4 shows",
      len(drafts) >= 2, f"openers seen: {drafts}")

# 4. Private shows get no draft
priv = public_show(private=True, title="Private Event", venue="Private Event")
check("private show -> empty draft", generate_description_draft(priv) == "")

# 5. Shows with DFW-Area-only city get no draft (can't geographically ground)
no_city = public_show(address_short="DFW Area")
check("DFW Area-only city -> empty draft (can't geographically ground)",
      generate_description_draft(no_city) == "")

# 6. Missing venue -> empty draft
no_venue = public_show(venue="")
check("missing venue -> empty draft", generate_description_draft(no_venue) == "")

# 7. Ticket-price variations
d_free = generate_description_draft(public_show(ticket_price="Free"))
check("Free ticket -> mentions 'No cover'", "No cover" in d_free)
d_paid = generate_description_draft(public_show(ticket_price="$25"))
check("Paid ticket -> mentions admission amount", "$25" in d_paid)


print("\n=== check_missing_info ===")

# 8. Public show without description -> flagged
miss = check_missing_info(public_show(), ev())
check("public show with no description field -> 'About-this-show description' missing",
      any("About-this-show description" in m for m in miss),
      f"missing list: {miss}")

# 9. Public show WITH description -> NOT flagged
miss2 = check_missing_info(public_show(description="Custom hand-written blurb"), ev())
check("public show with description -> no description miss",
      not any("About-this-show description" in m for m in miss2),
      f"missing list: {miss2}")

# 10. Private show without description -> NOT flagged (descriptions don't apply)
priv2 = public_show(private=True, title="Private Event")
miss3 = check_missing_info(priv2, ev())
check("private show with no description -> description miss NOT flagged",
      not any("About-this-show description" in m for m in miss3),
      f"missing list: {miss3}")

# 11. Empty-string description counts as missing
miss4 = check_missing_info(public_show(description=""), ev())
check("empty-string description -> flagged as missing",
      any("About-this-show description" in m for m in miss4))

# 12. Whitespace-only description counts as missing
miss5 = check_missing_info(public_show(description="   \n  "), ev())
check("whitespace-only description -> flagged as missing",
      any("About-this-show description" in m for m in miss5))


print("\n=== approval_token / build_approval_email_section (B32 / R25 Part A) ===")

# 13. Token is stable across calls for same (show, draft)
show_a = public_show()
draft_a = generate_description_draft(show_a)
t1 = approval_token(show_a, draft_a)
t2 = approval_token(show_a, draft_a)
check("approval_token is stable across calls for same inputs",
      t1 == t2 and len(t1) == 12,
      f"t1={t1} t2={t2} len={len(t1)}")

# 14. Token differs when draft changes (invalidates stale approvals)
t_different = approval_token(show_a, draft_a + " extra sentence.")
check("approval_token changes when draft text changes",
      t_different != t1,
      f"t1={t1} t_different={t_different}")

# 15. Token differs when show changes (can't cross-apply approvals)
show_b = public_show(date="2026-09-05", venue="3 Nations Brewing")
draft_b = generate_description_draft(show_b)
t_show_b = approval_token(show_b, draft_b)
check("approval_token changes when show changes",
      t_show_b != t1,
      f"t1={t1} t_show_b={t_show_b}")

# 16. Email section contains APPROVE + EDIT mailto links with token in subject
section = build_approval_email_section(show_a, draft_a, "info@liveradiodfw.com")
check("approval email section contains APPROVE mailto with token in subject",
      f"mailto:info@liveradiodfw.com?subject=APPROVE%20{t1}" in section,
      f"section: {section[:200]}...")
check("approval email section contains EDIT mailto with token in subject",
      f"subject=EDIT%20{t1}" in section,
      "EDIT mailto not found or missing token")
check("approval email section contains the draft text",
      draft_a in section)
check("approval email section contains bare token for Part B reference",
      f"Approval token: {t1}" in section)

# 17. Section is pure ASCII (cardinal rule)
try:
    section.encode("ascii")
    ascii_clean = True
except UnicodeEncodeError:
    ascii_clean = False
check("approval email section is pure ASCII (no em-dashes, no unicode)",
      ascii_clean)

# 18. Section contains no em-dash and no smart quotes (cardinal rule)
forbidden = ["\u2014", "\u2013", "\u2018", "\u2019", "\u201c", "\u201d"]
no_forbidden = not any(ch in section for ch in forbidden)
check("approval email section contains no em/en-dash or smart quotes",
      no_forbidden)


print()
if failures:
    print(f"FAILED: {len(failures)} case(s)")
    for label, detail in failures:
        print(f"  - {label}  {detail}")
    sys.exit(1)
else:
    print("PASSED: all cases")
