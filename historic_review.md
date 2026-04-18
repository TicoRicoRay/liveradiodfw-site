# Historic Calendar Import Review — 2021-04-01 to 2024-08-08

**Source:** Band Google Calendar (info@liveradiodfw.com) via webhook
**Total raw events in window:** 650
**Filter results:**
- `is_gig_event()` passed: **12**
- Skipped but confidence "likely gig": **38**
- Skipped as ambiguous (no strong signal): **164**
- Skipped as noise (rehearsals, medical, travel, birthdays): **436**

The existing `is_gig_event()` filter is tuned for the current "LR -" prefix convention, but historic events used bare venue names, so it missed most of them.

---

## Tier 1 — HIGH CONFIDENCE (50 gigs)

These have a clear venue match in title or location. Proposed for bulk import unless you flag any.

| # | Date | Title | Venue |
|---|------|-------|-------|
| 1 | 2021-04-17 | The Frisco Bar | The Frisco Bar & Grill |
| 2 | 2021-05-09 | INXS Tribute | The Box Garden at Legacy Hall |
| 3 | 2021-07-09 | Jackson Crossing @ Watters Creek | Watters Creek |
| 4 | 2021-07-17 | Frisco Bar & Grill | The Frisco Bar & Grill |
| 5 | 2021-10-09 | Frisco Bar & Grill | The Frisco Bar & Grill |
| 6 | 2021-10-16 | Lion & Crown | Lion & Crown Allen |
| 7 | 2021-11-13 | The Lion & Crown | Lion & Crown Allen |
| 8 | 2021-12-12 | Harvest Hall | Harvest Hall |
| 9 | 2021-12-18 | The Frisco Bar | The Frisco Bar & Grill |
| 10 | 2022-01-08 | Frisco Bar & Grill | The Frisco Bar & Grill |
| 11 | 2022-02-26 | Harvest Hall | Harvest Hall |
| 12 | 2022-04-02 | FRESH by Brookshires | FRESH by Brookshire's |
| 13 | 2022-04-09 | Frisco Bar & Grill | The Frisco Bar & Grill |
| 14 | 2022-06-11 | Lion & Crown | Lion & Crown Allen |
| 15 | 2022-06-25 | FRESH by Brookshires | FRESH by Brookshire's |
| 16 | 2022-07-02 | Powder Creek Pavillion | Powder Creek Pavilion |
| 17 | 2022-08-06 | FRESH by Brookshires | FRESH by Brookshire's |
| 18 | 2022-08-26 | Harvest Hall | Harvest Hall |
| 19 | 2022-10-08 | Frisco Bar & Grill | The Frisco Bar & Grill |
| 20 | 2022-10-15 | Fresh by Brookshires | FRESH by Brookshire's |
| 21 | 2022-11-13 | Lion & Crown Allen | Lion & Crown Allen |
| 22 | 2022-11-19 | Lion & Crown Addison | Lion & Crown Addison |
| 23 | 2022-12-31 | Sweet Water Grill | Sweetwater Grill |
| 24 | 2023-01-07 | Frisco Bar & Grill | The Frisco Bar & Grill |
| 25 | 2023-01-21 | Third Rail @ Harvest Hall | Harvest Hall — Third Rail |
| 26 | 2023-02-25 | Sweetwater Grill | Sweetwater Grill |
| 27 | 2023-03-18 | Lion & Crown | Lion & Crown Addison |
| 28 | 2023-03-25 | Frisco Bar & Grill | The Frisco Bar & Grill |
| 29 | 2023-04-01 | Wedding @ Legacy Hall | Legacy Hall (wedding) — **confirm: was this a gig?** |
| 30 | 2023-04-08 | Fresh by Brookshires | FRESH by Brookshire's |
| 31 | 2023-05-06 | Fresh by Brookshires | FRESH by Brookshire's |
| 32 | 2023-05-13 | Rockin S | Rockin' S at Twin Coves Marina |
| 33 | 2023-07-01 | Sweetwater Grill | Sweetwater Grill |
| 34 | 2023-07-15 | Jackson Crossing @ Harvest Hall Third Rail | Harvest Hall — Third Rail |
| 35 | 2023-07-29 | Fresh by Brookshires | FRESH by Brookshire's |
| 36 | 2023-08-12 | Frisco Bar & Grill | The Frisco Bar & Grill |
| 37 | 2023-08-19 | Risky Business at The Village Dallas | The Village Dallas |
| 38 | 2023-09-03 | Lion & Crown Allen | Lion & Crown Allen |
| 39 | 2023-09-24 | Risky Business - Private Party | (Private Event, Dallas) |
| 40 | 2023-09-30 | Risky Business @Third Rail | Harvest Hall — Third Rail |
| 41 | 2023-10-15 | Lion & Crown Allen | Lion & Crown Allen |
| 42 | 2023-12-03 | JC Private Event — Homebank Texas Company Party | Rusted Rail Golf (Private Event) |
| 43 | 2024-01-06 | Frisco Bar & Grill | The Frisco Bar & Grill |
| 44 | 2024-03-16 | Frisco Bar & Grill | The Frisco Bar & Grill |
| 45 | 2024-04-13 | Risky Business - Shakertins in Prosper | Shakertins Prosper |
| 46 | 2024-06-22 | Fresh Fate | FRESH by Brookshire's |
| 47 | 2024-06-28 | Rockin S Hidden Cove | Rockin' S Hidden Cove |
| 48 | 2024-07-20 | RB GIG — Lion & Crown Addison | Lion & Crown Addison |
| 49 | 2024-07-21 | Charlie's Lakeside at Pier 121 | Charlie's Lakeside |
| 50 | 2024-07-27 | Rockin S Hidden Cove | Rockin' S Hidden Cove |

---

## Tier 2 — MEDIUM CONFIDENCE (8 new-venue gigs)

These look like gigs at venues we've never had on the site. New venues require canonicalization entries.

| Date | Title | Location |
|------|-------|----------|
| 2021-07-24 | Plano Sports Tavern (formerly The Franchise) | 3000 Custer Rd, Plano, TX |
| 2021-10-03 | Plano Sports Tavern | same |
| 2021-10-31 | Plano Sports Tavern | same |
| 2021-11-07 | American Legion Post 597 | 1024 S Elm St, Carrollton, TX |
| 2022-02-13 | American Legion Post 597 | same |
| 2022-04-17 | American Legion Post 597 | same |
| 2022-01-16 | The Maverick | 1616 W Hebron Pkwy, Carrollton, TX |
| 2022-06-04 | Maverick | same |
| 2022-07-30 | Maverick | same |
| 2022-03-20 | Howling Mutt Brewpub | 205 N Cedar St, Denton, TX |
| 2022-04-01 | Lava Cantina | 5805 Grandscape Blvd, The Colony, TX |
| 2022-07-31 | Bob Riggins 65th | Turning Point Beer, Bedford, TX (private) |
| 2022-10-09 | Johnny Krackers | 501 E Moore Ave, Terrell, TX |
| 2022-10-23 | Women in Need Glow Run | Harry Myers Park, Rockwall, TX (charity?) |
| 2023-03-05 | Horsemen's Bar-B-Que | 1680 S State Hwy 121, Lewisville, TX |

---

## Tier 3 — PROBABLY NOT GIGS (needs your call)

| Date | Title | Why excluded |
|------|-------|--------------|
| 2022-10-15 | Fleetwood X | Different band playing; venue isn't the booking |
| 2024-01-26 | Red Line Drift Gig | Unclear — different band? |
| 2023-10-14 | Drum Clinic in North Richland Hills | Probably attending, not playing |
| 2023-12-14 | Bevs cmpany X-mas party | Could be gig at Dee Lincoln Prime |
| 2023-12-21 | Bancroft X-mas Party | Private xmas gig? |

---

## Questions for you

1. **Tier 1 — any you want excluded?** (Default is: import all 50.)
2. **Tier 2 — which of the 15 new-venue gigs are real?** Or just skip new venues entirely for now and only import Tier 1 (50)?
3. **Tier 3 — any of these 5 actually gigs?**
4. **Show titles** — prior-band-names like "Jackson Crossing" and "Risky Business" will be stripped per our sanitize rule, so the output titles will just be the venue. OK?
5. **Descriptions** — the 50 Tier 1 gigs will use the same machine-generated draft template we used for the 6 drafts in R15. OK?
