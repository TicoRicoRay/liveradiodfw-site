# Live Radio DFW - Roadmap

_Last updated: 2026-04-17_

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
