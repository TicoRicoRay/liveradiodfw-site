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

### R5. Historic shows migration
Bandzoogle staging (`https://liveradiodfw.bandzoogle.com`) and The Bash profile still hold the full historical show archive. Migrate into `/shows/` as permanent pages for long-tail SEO and credibility.

**Plan:**
- Pull show history from Bandzoogle staging calendar
- Pull show history from The Bash profile
- Generate one static page per historical show (same template as current shows)
- Add to `sitemap.xml`

**Priority:** Medium. Good for SEO, not urgent.

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
