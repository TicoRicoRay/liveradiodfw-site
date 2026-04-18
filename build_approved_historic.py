#!/usr/bin/env python3
"""
build_approved_historic.py — consolidate Ray's Tier 1 + Tier 2 approvals
into one approved_historic.json for import_historic.py to consume.

Tier 1 source: calendar_historic_candidates.json (50 entries, by eventId)
Tier 2 source: calendar_historic_ambiguous.json (164 entries, filter by date)

Outputs approved_historic.json with added fields:
  - tier: 1 or 2
  - privacy: "public" or "private" (drives is_private flag)
  - excluded: bool (#2 INXS is the only one)
"""

import json
from pathlib import Path

BASE = Path(__file__).parent

# Tier 1 decisions (indexed from calendar_historic_candidates.json, 1-based)
TIER1_DECISIONS = {}
for i in range(1, 51):
    TIER1_DECISIONS[i] = "public"
TIER1_DECISIONS[2] = "excluded"   # 2021-05-09 INXS Tribute
TIER1_DECISIONS[29] = "private"   # 2023-04-01 Wedding @ Legacy Hall
TIER1_DECISIONS[39] = "private"   # 2023-09-24 Royalton Dr Dallas
TIER1_DECISIONS[42] = "private"   # 2023-12-03 Homebank Texas @ Rusted Rail

# Tier 2 decisions (date-keyed — unique in the ambiguous file for our purposes)
# Each value: ("public"/"private"/"excluded", title_fragment_to_match)
TIER2_DECISIONS = [
    ("2021-07-24", "Plano Sports Tavern",    "public"),
    ("2021-10-03", "Plano Sports Tavern",    "public"),
    ("2021-10-31", "Plano Sports Tavern",    "public"),
    ("2021-11-07", "American Legion",         "public"),
    ("2022-01-16", "Maverick",                "public"),
    ("2022-02-13", "American Legion",         "public"),
    ("2022-03-20", "Howling Mutt",            "public"),
    ("2022-04-01", "Lava Cantina",            "public"),
    ("2022-06-04", "Maverick",                "public"),
    ("2022-07-30", "Maverick",                "public"),
    ("2022-07-31", "Bob Riggins",             "private"),  # 65th birthday
    ("2022-10-09", "Johnny Krackers",         "public"),
    ("2022-10-23", "Glow Run",                "public"),
    ("2023-03-05", "Horsemen",                "public"),
]


def main():
    candidates = json.loads((BASE / "calendar_historic_candidates.json").read_text())
    ambiguous  = json.loads((BASE / "calendar_historic_ambiguous.json").read_text())

    approved = []

    # Tier 1
    for i, e in enumerate(candidates, 1):
        decision = TIER1_DECISIONS.get(i, "public")
        if decision == "excluded":
            continue
        approved.append({
            **e,
            "tier": 1,
            "privacy": decision,
        })

    # Tier 2 — find by date + title fragment
    for date_str, title_frag, decision in TIER2_DECISIONS:
        if decision == "excluded":
            continue
        match = None
        for e in ambiguous:
            if e["start"][:10] == date_str and title_frag.lower() in e.get("title", "").lower():
                match = e
                break
        if not match:
            print(f"⚠ Tier 2 not found: {date_str} | {title_frag}")
            continue
        approved.append({
            **match,
            "tier": 2,
            "privacy": decision,
        })

    approved.sort(key=lambda x: x["start"])
    out = BASE / "approved_historic.json"
    out.write_text(json.dumps(approved, indent=2) + "\n")

    # Report
    t1_pub = sum(1 for a in approved if a["tier"] == 1 and a["privacy"] == "public")
    t1_priv = sum(1 for a in approved if a["tier"] == 1 and a["privacy"] == "private")
    t2_pub = sum(1 for a in approved if a["tier"] == 2 and a["privacy"] == "public")
    t2_priv = sum(1 for a in approved if a["tier"] == 2 and a["privacy"] == "private")
    print(f"Tier 1 public:  {t1_pub}")
    print(f"Tier 1 private: {t1_priv}")
    print(f"Tier 2 public:  {t2_pub}")
    print(f"Tier 2 private: {t2_priv}")
    print(f"Total approved: {len(approved)}")
    print(f"Written to {out}")


if __name__ == "__main__":
    main()
