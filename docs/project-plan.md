# Live Radio DFW — Project Plan

_Last updated: 2026-04-17 · 11:38 AM Central_


## 🚀 Starting a new session

Perplexity threads are disposable. This repo is the durable memory. To get a new agent up to speed fast, paste this as your first message:

> **Band marketing work on Live Radio DFW. Before anything else, read https://github.com/TicoRicoRay/liveradiodfw-site/tree/docs — start with `docs/project-plan.md` (especially "Pick up here next session"), then skim `docs/architecture/sources-of-truth.md` and `docs/runbooks/`. Then [today's task].**

**Rules of engagement you should remind the agent of if they slip:**
- Google Calendar is the source of truth for shows. Never hand-edit `shows.json` or `shows/*.html`.
- Venue contacts + negotiations live in **Mailchimp**.
- DNS is on **Cloudflare** (GoDaddy is registrar only).
- **Never read the EOS calendar** — it's personal and unrelated to the band.
- Always say **"Central"** or **"America/Chicago"** — never CDT/CST.
- Fix the foundation before the wall decorations.

---


## 🔖 Pick up here next session

_Put this at the top so next-session-me reads it first._

**Context:** We spent today (2026-04-17) fixing the sync-wipe bug (non-destructive merge + strict parser), grandfathering "Tickets: Free" into the calendar, moving docs to a `docs` branch on `liveradiodfw-site`, cleaning up the `-marketing` repo, and rewriting the DNS/Pages runbook.

**Top priority open items (in order):**

1. **Make the sync schedule DST-safe** (open item #6). **Resolved where it runs:** it's a Perplexity scheduled task (schedule_cron) created by a prior-session me. Each run costs credits. Fires at fixed UTC (13:11 UTC), so it's 8:11 AM Central in summer but 7:11 AM Central in winter — 1-hour drift twice a year. Fix: Ray opens Perplexity scheduled tasks view, finds the sync task, we update it to a Central-aware schedule from whichever thread owns it.

2. **Bandzoogle domain migrations** (open item #1). Still blocks canceling Bandzoogle subscription.

3. **Wildcard 301s for cached URLs** (open item #2). Waiting on Google Search Console list from Ray.

**Don't break:**
- The band Google Calendar is the source of truth for shows. Never hand-edit `shows.json` or `shows/*.html`.
- The EOS calendar is NOT band-related. Never touch it. Ever.
- Venue contacts live in **Mailchimp**, not this repo.
- DNS lives in **Cloudflare**, not GoDaddy.
- `liveradiodfw.com` is served from the `gh-pages` branch (with CNAME → `www.liveradiodfw.com`). The `docs` branch is never served.

**Nomenclature:** Always say "Central" / "America/Chicago". Never CDT/CST.

**Ray's pet peeves that matter:**
- "Not EOS" (don't read his EOS calendar looking for band stuff)
- "Fix foundation before wall decorations" (don't add features until the base is solid)
- "We're doing surgery here" (be precise, no guessing)
- Never promise "15 minutes"

---


## Open items

### 1. Migrate old band domains off Bandzoogle (BLOCKS Bandzoogle cancellation)
Bandzoogle Domain Manager shows 3 domains currently attached:
- `liveradiodfw.com` (PRIMARY) — **already moved** to Cloudflare → GitHub Pages
- `jacksoncrossingdallas.com` — still pointed at Bandzoogle
- `riskybusinessdfw.com` — still pointed at Bandzoogle

**Action:**
- Add both old domains as sites in Cloudflare (same nameserver swap pattern as liveradiodfw.com)
- Create Cloudflare Bulk Redirects (or Page Rules) sending all traffic to `https://www.liveradiodfw.com/lander`
- Remove both domains from Bandzoogle Domain Manager
- Then cancel Bandzoogle subscription

### 2. Wildcard 301 for other cached URLs (non-`/home`, non-`/lander`)
Google has cached individual old show pages.

**Recommendation: Cloudflare Bulk Redirects (Free plan)**
- Free plan allows one redirect list, up to 20 redirects
- Can pattern-match known old paths → `/` (homepage) or `/shows`
- Preserves link equity; eliminates soft 404s
- Alternative: Single catch-all Page Rule `liveradiodfw.com/*show*` → `/shows` (Free plan has 3 page rules)

**Status:** Deferred until we pull the full list of cached URLs from Google Search Console.

### 3. Historic shows migration (SEO)
Bandzoogle staging (https://liveradiodfw.bandzoogle.com) plus The Bash profile still hold the historical show archive. Migrate them into `/shows/` as permanent pages for long-tail SEO and credibility.

**Action:**
- Pull show history from Bandzoogle staging calendar
- Pull show history from The Bash profile
- Generate one static page per historical show (same template as current shows)
- Add to sitemap.xml

### 4. Google Search Console cleanup
- Submit updated sitemap.xml
- Request re-indexing of `/home` redirect + `/lander`
- Use URL inspection to force refresh on cached dead URLs

### 5. Verify GitHub Pages domain challenge TXT
The `_github-pages-challenge-TicoRicoRay` TXT record that was in the original DNS checklist is no longer present (may have been dropped during the Cloudflare migration). Low-urgency because the site is working and Cloudflare proxy protects against most takeover scenarios, but GitHub may eventually require re-verification.

**Action:** Pull fresh challenge value from `liveradiodfw-site` → Settings → Pages, and add as a TXT record in Cloudflare.

### 6. Verify the `sync_calendar.py` scheduled task and make it DST-safe
**Resolved location (2026-04-17):** The sync runs as a **Perplexity scheduled task** (created by a prior-session me via `schedule_cron`). It is NOT on Ray's Windows box, NOT a GitHub Action, and NOT on any external server. Each run costs Perplexity credits.

- Fires around 13:11 UTC daily (≈ 8:11 AM Central in summer, but UTC-fixed — will fire at 7:11 AM Central in winter when CST returns).
- Commits as `LiveRadioDFW <info@liveradiodfw.com>` via HTTPS+PAT, unsigned.
- **The cron is not visible from this thread** — `schedule_cron(list)` returns empty here. It lives in whichever earlier thread originally created it.

**Action:**
- Ray: open the Perplexity "scheduled tasks" view in the app, find the task (named something like "LiveRadioDFW calendar sync" or "daily sync"), and note which thread owns it.
- From that owning thread, update the schedule to use a Central-aware cron expression so 8 AM Central is stable across DST. Current fixed-UTC schedule means a 1-hour drift every November/March.
- Document the owning thread + task name in [architecture/calendar-sync.md](architecture/calendar-sync.md).

**Why it matters:** If the cron runs at a fixed UTC time, it will drift by one hour in winter (fires at 7:11 AM Central instead of 8:11). Not a fire, but worth fixing.

**Action:**
- Locate where the sync runs (check Ray's Windows Task Scheduler, any Linux boxes, GitHub Actions in the repo, etc.)
- If on Linux cron: add `CRON_TZ=America/Chicago` at top of crontab so `0 8 * * *` stays DST-correct
- If on Windows Task Scheduler: already tracks local time, just verify trigger is set to Central
- If GitHub Actions: use a timezone-aware action or accept the winter shift
- Once located, document in [architecture/calendar-sync.md](architecture/calendar-sync.md)

### 7. Timezone convention
Going forward: all documentation uses **"Central"** or **"America/Chicago"**, never "CDT" or "CST". The DST-named variants cause ambiguity and silent off-by-an-hour bugs.

## Recently completed

### 2026-04-17 (morning)
- ✅ Site back online via Cloudflare → GitHub Pages
- ✅ `/lander` page built from Bandzoogle staging copy (merger announcement) + hero image
- ✅ `/home` meta-refresh redirect to `/` (covers Google-cached /home URL)
- ✅ OG Cellars ticket price restored ($25)
- ✅ Grandfathered "Tickets: Free" into Google Calendar for all 7 public non-OG-Cellars shows
- ✅ Watters Creek 6/6 manually updated in Google Calendar UI (webhook can't touch Outlook-native IDs)
- ✅ `sync_calendar.py` patched:
  - Non-destructive merge (preserves hand-curated fields like `description`)
  - Strict ticket-price parser (blank + alert instead of silent "Free")
- ✅ Dry-run verification: 10 shows, 10 events, 0 drift, 0 alerts
- ✅ Postmortem written (Chapter 2: Apr 16-17 outage + Cloudflare fix, plus sync-wipe incident)

### 2026-04-17 (afternoon)
- ✅ `docs` branch established on `liveradiodfw-site` (README, project plan, runbooks, architecture, postmortem)
- ✅ `architecture/sources-of-truth.md` — canonical map of where each data type lives (calendar, Mailchimp, etc.)
- ✅ `architecture/marketing-automation.md` — monthly availability-email data flow
- ✅ `architecture/calendar-sync.md` — show-sync data flow
- ✅ `runbooks/edit-ticket-prices.md` — how to edit ticket prices via Google Calendar
- ✅ `runbooks/dns-and-pages.md` — rewritten from stale `-marketing/GITHUB_PAGES_CHECKLIST.md` to match current Cloudflare→GH Pages architecture
- ✅ Removed stale `CNAME` and stale `GITHUB_PAGES_CHECKLIST.md` from `-marketing`
- ✅ `-marketing/README.md` rewritten — clarifies repo roles, cross-links to docs branch

### 2026-04-17 (late morning)
- ✅ Swept all docs-branch files to use "Central" instead of CDT/CST (DST-safe terminology)
- ✅ Identified that `LiveRadioDFW` GitHub identity owns the daily auto-sync cron (location TBD — see open item #6)

## Architecture notes

- **Shows / gigs:** Google Calendar is the source of truth. See [architecture/calendar-sync.md](architecture/calendar-sync.md).
- **Venues + contacts:** Mailchimp is the source of truth (negotiations, booking history, contact info). See [architecture/sources-of-truth.md](architecture/sources-of-truth.md).
- **Website content:** `gh-pages` branch of this repo.
- **Docs:** `docs` branch of this repo (where you are).
