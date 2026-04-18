# Live Radio DFW - Roadmap

_Last updated: 2026-04-18_

Future plans, grouped by theme. Things we've decided or want to do but haven't scheduled.

For live defects, see [bugs.md](bugs.md). For session-to-session handoff and "pick up here next time", see [project-plan.md](project-plan.md).

---

## How to add a roadmap item (READ BEFORE ADDING)

### 1. This list is for PLANNED WORK only

Not defects. Not urgent patches. If it's broken, it belongs in [bugs.md](bugs.md) with a **B** prefix (or **J** if it's a Jarvis limitation). If it's something Ray wants to discuss before deciding, it belongs in [project-plan.md](project-plan.md) under "Pending discussion" with a **D** prefix.

### 2. Pick the next sequential R number

Scan all existing `### R<n>.` headings in this file, find the highest number, add 1. No reuse, no skipping.

### 3. Use this entry template

```
### R<n>. <Short title, no period>

<1-3 sentences of context: what's the goal and why.>

**Plan:** (or **Action:** / bullet list of steps)

**Depends on:** Anything that must happen first. "None" is valid.

**Priority:** High / Medium / Low / Parked.
```

Group under the right theme heading (Ops / infrastructure, SEO / content, Marketing automation, Decisions pending, Parked / someday-maybe). Create a new theme section only if the item genuinely doesn't fit an existing one.

### 4. Commit message format

```
docs: add R<n> - <short title>
```

### 5. After adding

- Commit to the `docs` branch, push
- Reply to Ray with the R ID and commit link
- If this item is high-priority and actionable now, also mention it in the "Top priorities right now" list in [project-plan.md](project-plan.md)

---

## Ops / infrastructure

### R1. Cancel Bandzoogle subscription ~~[OPEN]~~ &rarr; **DONE 2026-04-18**
Both legacy domains (`jacksoncrossingdallas.com`, `riskybusinessdfw.com`) are already Cloudflare-redirected to `/lander`. Remaining work (all completed):
- ~~Remove both domains from Bandzoogle Domain Manager (if still listed)~~
- ~~Cancel the Bandzoogle plan~~
- ~~Verify redirect rules land on `https://www.liveradiodfw.com/lander` (HTTP 301)~~

**Closed 2026-04-18:** Ray closed the Bandzoogle account. Recurring subscription cost eliminated. Legacy-domain redirects to `/lander` were already in place via Cloudflare before cancellation; no infra change required on our side. If either legacy domain ever drops out of DNS control, `/lander` is still the canonical merger-announcement landing and can be pointed at from any new source.

**Priority:** ~~High - recurring subscription cost is the motivator.~~ N/A (closed).

### R2. UptimeRobot monitoring
Set up UptimeRobot (free tier) for `https://www.liveradiodfw.com` with SMS + email alerts. Currently a checkbox in the DNS/Pages runbook but not provisioned. Catches outages like the 2026-04-15 event faster than Google Search Console noticing.

**Priority:** Medium. Low effort.

### R11. Extend `build_includes.py` to cover head-level snippets

**Why:** The site is about to grow from ~15 top-level pages to many more (R5 historic-show migration alone will add dozens of individual show pages, and we have ongoing plans for more SEO/landing pages). Today `build_includes.py` owns nav and footer as single points of maintenance via `<!-- BEGIN_NAV -->` / `<!-- BEGIN_FOOTER -->` markers, but the inline `<head>` script (theme bootstrap, and soon anything else we want uniform across the site) is still hand-copied into every `.html` file and also generated inline inside `build_show_pages.py`. Every new page Ray adds is a fresh copy of head content that can drift. Every fix to that content (like B12, the theme-persistence bug) means touching 15+ files.

**Scope:** Add a third include marker pair `<!-- BEGIN_HEAD_BOOT -->` / `<!-- END_HEAD_BOOT -->` served from `includes/head-boot.html`. Move the theme bootstrap there as the first tenant. Reuse the same pattern for future head-level content we want consistent site-wide (cache-bust version string, analytics snippet if we ever add one, shared meta defaults, favicon block, preload/preconnect hints).

**Also:** Update `build_show_pages.py` to read from the same `includes/head-boot.html` instead of inlining its own copy of the bootstrap script, so show-detail pages and top-level pages stay in sync.

**Priority:** High-leverage, low-effort. Worth doing **before** B12's fix lands so the B12 patch is a single-file edit to `includes/head-boot.html` instead of a 15-file sweep. Also makes future template-level bugs ("add viewport tag to all pages", "update cache-bust v=") similarly trivial.

**Depends on:** Nothing. Can ship standalone.

---

### R3. Google Search Console cleanup
- Submit updated `sitemap.xml`
- Request re-indexing of `/home` redirect + `/lander`
- URL-inspection sweep of cached dead URLs to force refresh

**Depends on:** Ray exports the cached-URL list from Search Console first.

---

## SEO / content

### R4. Wildcard 301s for cached URLs
Google has cached individual old show pages. Cloudflare Bulk Redirects (Free plan: one list, up to 20 redirects) pattern-match known old paths → `/` or `/shows`. Alternative: single catch-all Page Rule `liveradiodfw.com/*show*` → `/shows`.

**Depends on:** R3 (need the cached-URL list from Google Search Console first).

### R5. Historic shows migration ~~[OPEN]~~ ~~[IN PROGRESS]~~ → **SHIPPED 2026-04-18 PM**
Bandzoogle staging (`https://liveradiodfw.bandzoogle.com`) and The Bash profile still hold the full historical show archive. Migrate into `/shows/` as permanent pages for long-tail SEO and credibility.

**Bandzoogle scope (confirmed 2026-04-18 via browser extract):**
- **33 past shows** across 2 pages: page 1 (20 shows, Apr 11 2026 → May 2 2025) + page 2 (13 shows, Apr 5 2025 → Aug 9 2024)
- Shows span ~20 months. Oldest is Aug 9 2024 at Harvest Hall Grapevine
- 4 shows from Aug-Sep 2024 are from the **Jackson Crossing** era (prior band name), caught via description text mentioning "Jackson Crossing"; we'll regenerate those descriptions via B16 draft path so they land with current voice rather than preserving the prior brand references
- 5 descriptions are truncated at ~95 chars by Bandzoogle's HTML with no "Read more" expansion available
- No ticket prices were recorded on Bandzoogle (not shown on any of the 33 past shows)

**Plan (this session, 2026-04-18):**
1. **Import layer (one-time):** new `lrdfw-ghpages/import_bandzoogle.py`. Reads the 33 shows, normalizes venue names against existing shows.json conventions (e.g. `"Fresh by Brookshires - Fate TX"` → `"FRESH by Brookshire's"`), extracts actual venue from address when the title is a marketing slogan, parses the actual venue address, sets `"past": true` + `"source": "bandzoogle-import-2026-04-18"`. Dedupes against any existing shows.json dates.
2. **Description strategy per B16 rollout:**
   - Bandzoogle description present and >= 50 chars and not truncated → use verbatim
   - Bandzoogle description missing, truncated, or mentions "Jackson Crossing" → B16 `generate_description_draft()` with `[DRAFT - ...]` flag; page renders placeholder until Ray approves
   - Private events → no description, same as current (handled naturally)
3. **Build layer:** extend `build_shows.py` to split shows into upcoming + past, stop rendering past on `/shows` and home; extend `build_show_pages.py` to render a subtle "Past show" banner and no Add-to-Calendar / Get-Directions CTAs (irrelevant for past shows).
4. **New index page:** `past-shows.html` (new file, built via a new builder) — reverse-chronological list of past shows, same card style as `/shows`. Linked from `/shows` and footer.
5. **Sitemap:** append all 33 past-show pages to `sitemap.xml`.
6. **Review gate:** after import + build generate local preview, pause and present the full list to Ray for batch approval BEFORE committing to gh-pages.

**The Bash profile (deferred, not this session):** a separate R-entry will be filed when we tackle that source.

**Priority:** Medium. Good for long-tail SEO and credibility. Blocking follow-up: description enrichment work will continue after the initial batch ships; high-value venues (repeat bookings, marquee shows) get hand-curated replacements over time.

**Status:** SHIPPED 2026-04-18 PM — 33 Bandzoogle shows live at https://www.liveradiodfw.com/past-shows.html. Commit `51da273` on gh-pages. Shipped breakdown: 22 verbatim (with prior-band-name sanitization), 6 machine-draft placeholders, 5 private events. Per Ray: shipping best-guess state and iterating on any that look off. Older-than-Bandzoogle shows (2021-2024) to be added as Ray digs them up — follow-up import will re-use `import_bandzoogle.py` with a fresh raw file.

**Follow-ups:**
- Thin Lion & Crown boilerplate descriptions (5 shows, ~62 chars each, near-identical) are good candidates for hand-curated rewrites if Ray wants more SEO depth on those pages.
- Next import batch: older shows Ray surfaces (pre-Aug 2024). Same script, new `bandzoogle_raw.json` (or analogous).

### R16. Historic calendar import (pre-Bandzoogle 2021–2024) → **SHIPPED 2026-04-18 PM**
63 past shows imported from the `info@liveradiodfw.com` Google Calendar covering 2021-04-16 through 2024-07-27 (all pre-date the R5 Bandzoogle earliest entry of 2024-08-09, so zero dedupe collisions). Shipped via new `import_historic.py` + `build_approved_historic.py` in the gh-pages repo.

**Breakdown:** 59 public + 4 private. All 59 public entries carry `[DRAFT - ...]` machine descriptions (internal calendar notes — booking fees, gate codes, contact numbers — are never shipped verbatim). Public pages render the "Show details coming soon" placeholder until Ray enriches them. shows.json grew 43→106; show pages 36→95; sitemap regenerated via new `update_sitemap.py`. Commit `100d182` on gh-pages.

**New canonical venues registered:** Plano Sports Tavern, The Maverick, American Legion Post 597, Howling Mutt Brewing, Lava Cantina The Colony, Turning Point Beer, Johnny Krackers, Harry Myers Park, Horsemen's Bar-B-Que, The Village Dallas, Shakertins Prosper, Rockin' S at Twin Coves.

**Follow-ups:** enrichment passes for the 59 placeholder pages, ideally grouped by venue (all Frisco Bars, all Lion & Crowns, etc.) for speed.

### R17. Upgrade calendar icons across the site
Replace the current calendar-date chips on the homepage, `/shows`, `/past-shows`, individual show pages, and future locale pages (see R18) with a polished HTML+CSS calendar-icon treatment inspired by [SitePoint's "Create a Calendar Icon in HTML5 and CSS3"](https://www.sitepoint.com/create-calendar-icon-html5-css3/) — month band across the top, large day number body, subtle dashed perforation, layered page-stack shadow for depth. Match our palette (B14 red-on-black dark mode + light-mode counterparts) instead of SitePoint's orange.

**Pattern from the reference (palette-swap target in parens):**
- Outer card: white bg (dark mode: `--surface`), rounded corners, multi-layer `box-shadow` stack for 3D page/binding effect
- Month band: top strip, solid fill (`--red`) with white text, dashed bottom border for the perforated-torn-edge look
- Day number: oversized (2.8em equivalent), dark text on light (light text on dark)
- Day name: small, bottom, in accent color
- All ems/percentages so it scales with `font-size` on the container

**Scope:**
- Audit every place a date pill renders today: `build_shows.py` full cards, compact cards, past-show cards, `show-page-meta` on individual show pages, home hero upcoming-shows strip.
- Build one reusable CSS component (`.cal-icon` with `.cal-icon__month`, `.cal-icon__day`, `.cal-icon__dow`) in `style.css` with light + dark theme variants.
- Update all builders/templates to emit the new markup. Bump `style.css?v=`.
- Verify in both palettes via `screenshot_page`.
- Accessibility: semantic `<time datetime="YYYY-MM-DD">` wrapper with `aria-label` like "Friday, July 23, 2021".

**Priority:** Medium. Visual polish, not critical path. Good candidate after a batch of placeholder descriptions get enriched (R16 follow-up) so the upgraded icons sit alongside real copy instead of placeholders.

### R18. Locale / "where we've played" pages
SEO long-tail: per-city landing pages (e.g. `/dfw-cover-band-frisco.html`, `/dfw-cover-band-plano.html`, `/dfw-cover-band-the-colony.html`) listing every show Live Radio DFW has played in that city, linking to the individual show pages. Builds on the R16 historic import which already tags every show with `address_short` ("Frisco, TX", "Plano, TX", etc.), so the data is ready.

**Plan sketch (not yet scoped):**
- New builder `build_locale_pages.py` that groups shows by city and renders one HTML per locale with the locale name in `<title>`, `<h1>`, and the intro copy.
- Template includes past-shows list for that city + any upcoming shows in the same city, plus a "book us in your town" CTA linking to `/book`.
- Candidate cities (by current show count): Frisco, Allen, Grapevine, Fate, Plano, The Colony, Addison, Carrollton, Royse City, Dallas, Lewisville. Filter to cities with ≥3 shows to avoid thin content.
- Add to `sitemap.xml`, link from footer or `/shows` page.
- Each page uses the R17 calendar-icon treatment on its show list.

**Depends on:** R16 historic import (done) supplies the show density per city.

**Priority:** Medium. Long-tail SEO play with real content (actual shows we played, not keyword stuffing) — exactly the kind of page Google and humans both like.

---

## Marketing automation

### R6. Merger intro campaign
Drafts exist in the `liveradiodfw-marketing` repo. Decide on timing and target audience (existing Jackson Crossing / Risky Business contacts, current Venues list, new-prospect list).

### R7. Setlist / theme analysis rollout
Analysis assets already live in `liveradiodfw-marketing`. Decide whether/how to expose on the public site (e.g., per-Station landing pages beyond the homepage Stations overview).

### R12. End-to-end booking links in the monthly availability email

Today the monthly availability email (generated by `liveradiodfw-marketing/liveradiodfw_availability.py` + Mailchimp template, Tuesday 9am Central, last-Tuesday-of-month) lists the band's open dates as plain text and asks the recipient to "reply" to book. Turn each open date into a "Book {date}" link that drops the venue contact into a pre-populated booking form on `liveradiodfw.com`, so a venue can commit without an email thread. Booking-manager adoption is unknown, but the friction delta (reply vs. one click) is real and low-cost to test.

**Plan:**
- New public page (e.g., `/book?date=YYYY-MM-DD&mc_id={MC_MERGE_TAG}`) with a form that already knows: the date being booked, the venue name, the contact's name, the contact's email, and — if Mailchimp has them as merge tags on the Venues list — prior-booking flag, house sound/lights policy, typical pay, load-in notes, stage size, PA details.
- Mailchimp template change: wrap each list item in an anchor with the date + Mailchimp merge tags in the query string so the landing page renders pre-filled.
- Form submit path: post to the existing Apps Script webhook (same endpoint that handles GCal writes) with a new action (e.g., `action="booking_request"`) that creates a tentative GCal event on `info@liveradiodfw.com` with the venue as attendee and emails Ray + the venue a confirmation. Or, simpler first pass: form submit just emails a structured booking request to Ray and logs to a Sheet; tentative GCal write comes later.
- Two-click-confirm pattern for Ray so a venue click doesn't auto-book without his ack.

**Design questions to settle before build:**
- Which Venues-list merge tags already exist in Mailchimp vs. need to be added? (sound/lights, pay, load-in, prior-booking).
- Does the form need to collect anything beyond what Mailchimp already knows? (set time, headcount expectation, specific ask).
- Tentative-event creation in GCal now vs. email-first now and GCal later.
- Analytics: we need click-through and form-submit tracking from day one to answer "do booking managers actually use this," otherwise the feature runs on faith the same way the current email does.

**Depends on:** B1 (DST cron alignment) should be settled first, since any link scheme ties to the exact send cadence. Mailchimp Venues-list merge-tag audit.

**Priority:** Medium. Cool factor is high, adoption is unknown, and the supporting data (merge tags, analytics) is a prerequisite. Ship after foundation items (R11, B12, B7 Part 2).

### R13. Style guide vs. site copy audit

The authoritative brand voice lives in `liveradiodfw-marketing/MARKETING_STYLE_GUIDE.md`, but site copy across `liveradiodfw-site` (home hero, Stations pages, about, press-kit body, booking page intro, error strings, footer taglines) was written piecemeal across many sessions without ever being checked against the guide. Likely drift in voice, terminology, and tone. One-time audit to catch drift, plus a checklist so future copy edits diff against the guide before landing.

**Plan:**
- Jarvis reads the style guide and extracts the hard rules (terminology, capitalization, forbidden words, voice descriptors, tagline variants).
- Jarvis diffs every user-facing string in `-site` against those rules and produces a findings doc in `docs/` with proposed edits, grouped by severity.
- Ray reviews, says yes/no per item, Jarvis lands the approved edits.
- Add a line to the end-of-session runbook: "if user-facing copy changed, diff it against the style guide."

**Depends on:** Nothing. Jarvis can run the audit solo and surface findings for review.

**Priority:** Low. No user-visible bug, but the drift compounds every session. Worth one clean pass.

### R14. Enrich press-kit and booking pages with marketing-repo content

`press-kit.html` exists as an EPK (bio, photos, stage plot) but does not surface the setlist theme analysis, merger narrative, or talent-buyer-oriented proof points (crowds drawn, venues played, price range, logistics). `book.html` is purely an inquiry form, not a sales page; there is no page aimed at a venue talent buyer asking "why should we book you over another band." The content to answer those questions now lives in `liveradiodfw-marketing` (setlist theme analysis, intro campaign drafts, style guide positioning).

**Plan:**
- **Press kit additions:** short "recent venues" strip (pulled from GCal history once R5 lands, hand-curated until then), press-style one-paragraph pitch sourced from the style guide, one-line set-length options (45/60/75/90/120 min), link to Videos page with a specific "if you only watch one" pin.
- **New "Why book us" page** (or a section added to `book.html` above the form): talent-buyer framing. Crowd we draw, markets we play, typical set structure, PA / monitoring self-sufficiency (in-ears noted), insurance, load-in realities, price range (even a "starts at" figure reduces dead-end inquiries). Setlist theme analysis gives us the raw material for "here's the catalog depth" claims that are specific, not fluffy.
- Keep the talent-buyer page distinct from fan-facing pages (home, songs, videos). Different audience, different tone.

**Depends on:** R13 (style guide audit) ideally ships first so the new copy lands already aligned to the guide instead of needing a rewrite pass.

**Priority:** Medium-high. Directly addresses the top of the booking funnel (a venue scout's first visit), which is more leverage than any single optimization to the existing pages.

---

## Decisions pending (not bugs, but blocking other work)

### R8. Regina as event attendee - method decision ~~[PENDING]~~ → **DECIDED 2026-04-17 PM (option b)**
See [bugs.md B2](bugs.md#b2-webhook-attendees-field-is-a-silent-no-op). Ray chose option (b): extend the `_updateEvent` webhook so automation can add attendees. R10 implemented the code change and it's deployed. The optional post-sync step in `sync_calendar.py` to auto-add Regina to every future public event is not yet implemented — if we want that, file a new R-entry for it rather than reopening R8.

### R9. Timezone convention enforcement
Standing rule: all docs use "Central" or "America/Chicago", never "CDT" or "CST". Swept once on 2026-04-17; worth a periodic grep to keep new docs compliant.

### R10. Extend `_updateEvent` to honor attendees ~~[OPEN]~~ → **DONE 2026-04-17 PM**
Dependency for [B2](bugs.md#b2-webhook-attendees-field-is-a-silent-no-op). `_updateEvent` previously accepted the `attendees` payload field but had no code path that acted on it.

**Delivered 2026-04-17 PM:**
1. ✅ Extended `_updateEvent` in `docs/scripts/LiveRadioDFWCalendar.gs` to iterate `data.attendees || data.guests` and call `event.addGuest(email)` for each.
2. ✅ Normalized `_createEvent` to accept either field name as a bonus.
3. ✅ Both paths now return the resulting `guests:` array in the response for verification.
4. ✅ Published as Version 2 via [runbooks/publish-calendar-webhook.md](runbooks/publish-calendar-webhook.md) (same session the passphrase was rotated for B7 — coordinated change).
5. ✅ Smoke-tested against a throwaway event: `create` with `attendees: ["rmyers@futurebright.com"]` returned `guests: ["rmyers@futurebright.com"]`; `update` with a new attendee set returned the updated `guests` array; throwaway deleted.
6. ✅ B2 moved to Fixed Recently.
7. ⏭️ Optional `sync_calendar.py` auto-ensure-Regina step deferred — file a new R-entry if we decide to do it.

---

## Parked / someday-maybe

- Individual band-member bios on `/about` (names, instruments, roles) - currently the site says only "5 vocalists." Requires photos + copy.
- Social handles on the site - currently none published.
- Set-length and typical-show specs on the site for booking leads.
- Band finances tooling - explicitly outside this repo.
