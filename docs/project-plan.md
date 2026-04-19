# Live Radio DFW — Project Plan

_Last updated: 2026-04-19 · 9:05 AM Central_

**This file is the session-to-session handoff.** For active defects see [bugs.md](bugs.md). For planned work see [roadmap.md](roadmap.md).


## 🚀 Starting a new session

Perplexity threads are disposable. This repo is the durable memory. To get a new agent up to speed fast, paste this as your first message:

> **Band marketing work on Live Radio DFW. Start the 60-min timer. Then: [today's task].**
>
> _Memory should carry: name (Jarvis), cardinal rules (EOS separation, Central not CDT/CST, no em-dashes, no "15 minutes" estimates, GCal source of truth for shows, Mailchimp for venue contacts, Cloudflare for DNS, `gh-pages` serves the site), and the docs-read trigger (on the phrase "Live Radio DFW" / "the band" / "band marketing", read https://github.com/TicoRicoRay/liveradiodfw-site/tree/docs - `docs/project-plan.md` first including "Pick up here next session", then `docs/bugs.md`, `docs/roadmap.md`, `docs/architecture/scheduled-tasks.md`, `docs/architecture/connectors.md` (which connectors are band-active vs. off-limits - critical because connectors are account-wide, not project-scoped), skim `docs/architecture/sources-of-truth.md` and `docs/runbooks/`, then the public site at https://www.liveradiodfw.com, and also review https://github.com/TicoRicoRay/liveradiodfw-marketing - the sibling marketing repo that hosts the monthly venue-availability Mailchimp automation, marketing style guide, and setlist theme analysis; `-site` and `-marketing` work together). Follow the "How to add" templates at the top of `bugs.md` / `roadmap.md` for any new bug or roadmap entry - no exceptions. "Wrap up" / "close out the thread" / "end of session" triggers the checklist at `docs/runbooks/end-of-session.md`._
>
> _The timer line is in the prompt because it's the most failure-prone startup step (see bugs.md J5). If a future thread skips the timer even with this prompt, that's a new J-entry._
>
> ---
>
> **Long fallback prompt (use if the short one fails):** Band marketing work on Live Radio DFW. Before anything else, read https://github.com/TicoRicoRay/liveradiodfw-site/tree/docs - start with `docs/project-plan.md` (especially "Pick up here next session"), then `docs/bugs.md` (active defects, including Jarvis's own blind spots in the J-series), `docs/roadmap.md` (planned work), and `docs/architecture/scheduled-tasks.md` (every running cron). Skim `docs/architecture/sources-of-truth.md` and `docs/runbooks/` - `docs/runbooks/end-of-session.md` is the checklist to run when I say "wrap up" or "close out the thread." For band-facing facts (genre, lineup, songs, upcoming shows, positioning, social handles), read the public site at https://www.liveradiodfw.com - that's the source of truth for anything the public sees. When adding to the bug list or roadmap, follow the "How to add" template and numbering rules at the top of `bugs.md` / `roadmap.md` - no exceptions. Start the 60-min timer. Then [today's task].

**Rules of engagement you should remind the agent of if they slip:**
- Google Calendar is the source of truth for shows. Never hand-edit `shows.json` or `shows/*.html`.
- **Band events are created in Google Calendar on `info@liveradiodfw.com` only — never in Outlook.** Outlook is email only for the band; its calendar is out of the band pipeline entirely (decommissioned 2026-04-17 PM, see `architecture/sources-of-truth.md` and B3 in `bugs.md`).
- Venue contacts + negotiations live in **Mailchimp**.
- DNS is on **Cloudflare** (GoDaddy is registrar only).
- **Never read the EOS calendar** — it's personal and unrelated to the band.
- Always say **"Central"** or **"America/Chicago"** — never CDT/CST.
- Fix the foundation before the wall decorations.
- **The 60-min timer is a check-in, not a hard stop.** Clarified by Ray 2026-04-17 PM: when Ray takes a break, that is Ray's break — Jarvis keeps working. At the 60-min mark Jarvis posts a brief check-in ("60 min mark, anything to adjust?") and keeps going unless Ray steers otherwise. The end-of-session checklist at `runbooks/end-of-session.md` runs ONLY on Ray's explicit wrap-up request — never automatically, never on timer expiry.

---


## 🔖 Pick up here next session

_Put this at the top so next-session-me reads it first._

**Context:** 2026-04-19 session was pure infrastructure cleanup. Opened a Bark.com bid for Ree's 6/7/26 birthday party (file in local workspace, not yet sent by Ray). Then ran a three-item sweep: **R2 closed** (UptimeRobot live on free plan, HEAD-only 5-min checks, alerts to info@, dashboard password-protected; HEAD-only means we cannot catch soft failures like 200-with-broken-body, which is a known paid-tier constraint we are explicitly accepting for this low-traffic marketing site). **R3 closed** (sitemap of 112 URLs submitted to GSC; `/lander` re-index requested; `/home` deduplicated via a Cloudflare Page Rule — zone is still on the legacy UI, so it is Page Rules not Redirect Rules for now — `*liveradiodfw.com/home*` → 301 → `https://www.liveradiodfw.com/` with preserve-query-string on; verified clean via curl across 7 variants covering apex/www, trailing slash, `.html`, query strings, case). **R9 closed** as a standing rule with two enforcement points: `audit_shows.py` catches CDT/CST in show data at build time, and a new **step 4 in `runbooks/end-of-session.md`** greps the session diff before every commit. First live test of the step-4 hook is this very commit. Step 4 surfaced real CDT strings at `gh-pages/sync_calendar.py:677` and `:731` in alert email bodies, which became **B17** (filed, not fixed — Ray will pick option from entry). New memory entry saved: SEO belt-and-suspenders preference (wildcard patterns covering apex/www, trailing slashes, file extensions, query strings) — applies to this project and all future web work.

**Heads-up for the NEXT thread specifically:** top-of-funnel foundation work (B7 Part 2, B1, R11, B6) is still untouched from prior sessions — this session was cleanup only, not foundation. R4 remains on ice until 2026-05-03 (waiting for Google to re-crawl after this session's /home 301).

**GSC connector is now live** (2026-04-19, 9:00 AM Central). Property: **`sc-domain:liveradiodfw.com`** (Domain property — the two URL-prefix variants return no data). Two tools exposed: `retrieve-site-performance-data` (search analytics) and `submit-url-for-indexing` (indexing API). Note for future sessions: sitemap management and URL Inspection API are **not** exposed by this Pipedream connector — if we ever need those, fall back to Ray doing it in the UI or look for a native GSC connector. First audit completed at 9:00 AM Central on break; findings filed as R19/R20/R21 and R4 enriched. See commits below.

**Top priorities right now:**

0. **R19 - `/lander` conversion audit (new 2026-04-19, medium).** `/lander` is ranking at avg position 32 for "dallas cover bands" and other high-intent queries with 0.9% CTR. Small content/meta edit could convert already-leaking traffic. See [roadmap.md#r19](roadmap.md).
1. **B7 - Part 2: move `sync_calendar.py` off `gh-pages`.** See [bugs.md#b7](bugs.md). Passphrase was rotated 2026-04-17 PM (Part 1), but the new value is still hard-coded in `gh-pages/sync_calendar.py` and therefore still fetchable at `https://www.liveradiodfw.com/sync_calendar.py` and GitHub raw. Relocate the sync script to a non-public host (likely Ray's Windows box; see B1) and read the passphrase from an env var or `.gitignore`d config file.
2. **B1 - DST-safe sync cron.** See [bugs.md#b1](bugs.md). Ray needs to find the owning thread in Perplexity's scheduled-tasks view. Naturally pairs with B7 Part 2 since both likely touch wherever the cron actually runs. Relevant new context: the real monthly availability cron lives in `-marketing`, not this repo - see `liveradiodfw-marketing/liveradiodfw_availability.py` and `setup_task_scheduler.ps1`.
3. **D1 - ChatGPT site audit.** See "Pending discussion" below. Ray has audit findings to walk through before they become bugs or roadmap items.
4. **R11 - head-level include extraction.** See [roadmap.md#r11](roadmap.md). High-leverage foundation item - makes future template-level fixes (like B12) single-file edits instead of 15-file sweeps. Ship before B12.
5. **R4 - Wildcard 301s.** See [roadmap.md#r4](roadmap.md). Reassess 2026-05-03 after Google re-crawls following this session's `/home` 301. R4 now enriched with concrete URL patterns from GSC audit: `.html` Bandzoogle variants (6 paths), `/event/<id>/<id>/<slug>` pattern (8 zombies observed), `http://` scheme variants, all reachable via 2-3 wildcard rules within Cloudflare free-plan limits.
6. **B6 - Videos two-click bug.** See [bugs.md#b6](bugs.md). Investigation-heavy; not a quick fix.
7. **R18 - Locale SEO landing pages.** See [roadmap.md#r18](roadmap.md). "Band-type in {city}" intent capture, leveraging R16 historic calendar as proof-of-presence. Medium-high leverage; queue behind foundation work and R4.
8. **R21 - Verify /home 301 consolidation.** See [roadmap.md#r21](roadmap.md). Fact-finding only, earliest check 2026-05-03. Natural pair with R4 reassessment on the same date.

**Recently closed:**
- **GSC audit 2026-04-19 — 3 new roadmap items filed, R4 enriched:** First run of the newly-connected `google_search_console__pipedream` connector, last 28 days (2026-03-22 → 2026-04-19). Key findings: (a) `/home` carried **61% of site clicks** pre-301 — the rule we shipped yesterday is consolidating more traffic than assumed, filed as R21 to verify after re-crawl; (b) `/lander` ranks (weakly) for exactly the high-intent commercial queries we care about ("dallas cover bands", "cover bands in dallas", "80s cover band dallas") but converts at 0.9% CTR, filed as R19 for a conversion audit; (c) station pages (`/the-classic-rock-station`, `/the-all-oldies-hits-station`) attract FM-radio-seeker traffic that doesn't convert to band booking — filed as R20 with four framing options for Ray; (d) concrete URL patterns for R4 (wildcard 301s) now documented with evidence (`.html` variants, `/event/<id>/<id>/<slug>` zombies, `http://` scheme variants). No bugs filed — all four findings are planned-work or vigilance items, not defects.
- **R2 - Uptime monitoring live (2026-04-19):** UptimeRobot free plan, 5-min HEAD checks on `https://www.liveradiodfw.com/`, email alerts to info@liveradiodfw.com, public dashboard password-protected. Known constraint: HEAD-only means soft failures (200 status with broken body) are not caught — keyword monitoring is paid-tier, explicitly deferred for this low-traffic marketing site. Commit `2fb0df9`.
- **R3 - GSC cleanup + /home deduplication (2026-04-19):** Sitemap (112 URLs) submitted to Google Search Console. `/lander` re-index requested. `/home` deduplicated via Cloudflare Page Rule `*liveradiodfw.com/home*` → 301 → `https://www.liveradiodfw.com/` (preserve query string on). Zone still on legacy Cloudflare UI so this is Page Rules not Redirect Rules. Verified clean via `curl -sI` across apex/www, trailing slash, `.html`, query strings, and case variants. Free plan, 1/3 Page Rules used. Runbook gained new Cloudflare Page Rules section. Commit `ff09e8d`.
- **R9 - Timezone convention enforcement (2026-04-19):** Standing rule, no ship date. Two enforcement points: `audit_shows.py` at build time catches CDT/CST in show data; new step 4 in `runbooks/end-of-session.md` greps session diff before every commit with explicit exception list (Python identifiers, rule-quoting text, linter examples). Sweep surfaced real violations at `sync_calendar.py:677` and `:731` (alert email bodies) which became B17. Commit `d4b57c1`.
- **B17 filed (2026-04-19):** `gh-pages/sync_calendar.py:677` and `:731` contain user-facing `CDT` strings in alert email bodies. Three fix options documented in the entry; recommended option 1+3 (replace with "Central" + pull the time-zone label from a single constant so it can't drift again). Low priority, two-line fix.
- **SEO belt-and-suspenders preference added to About Ray (2026-04-19):** Wildcard patterns covering apex/www, trailing slashes, file extensions, and query strings. Applies to this project and all future web projects. Rule-of-thumb for easily-forgettable set-and-forget work: leave a solid foundation the next person can't accidentally undo.
- **D2 - Keep markdown, don't adopt GitHub Issues/Projects/Wiki (2026-04-18 midday):** Explored pros/cons of migrating B/J/R/D entries from markdown to GitHub Issues. Decision: keep markdown. Primary reason is the per-session tool-call tax (1 call today vs 3-16 for equivalent Issues flow) versus marginal UI benefit for a two-actor team. Projects is ceremony without payoff at our scale; Wiki decouples docs from code, which is backward. Revisit triggers documented in D2 entry. See [project-plan.md D2](project-plan.md).
- **R12, R13, R14 filed (2026-04-18 midday):** R12 end-to-end booking links in availability email (medium priority, depends on B1 and a Mailchimp merge-tag audit; ship after foundation). R13 style guide vs site copy audit (low priority, Jarvis can run solo). R14 press-kit and booking page enrichment with marketing-repo content (medium-high, top-of-funnel leverage, ideally after R13). See [roadmap.md](roadmap.md).
- **Marketing style guide Section 11 - one-primary-CTA guideline (2026-04-18 midday, `-marketing` commit `71df18f`):** Added to `MARKETING_STYLE_GUIDE.md` in the `-marketing` repo. Codifies the March 2026 email rebuild learning as a guideline (not a rule) with explicit deviation-is-welcome language, baseline data points, and what-to-watch triggers for future sends. Section 10 checklist cross-references Section 11.
- **Startup prompt updated for `-marketing` sibling repo (2026-04-18 midday, `-site` docs commit `660b511`):** The docs-read trigger in this file's startup prompt now loads both `-site` and `-marketing` on thread start. Memory entry updated in parallel.
- **B8 - Private-event filter broadened to word-boundary match (2026-04-18 midday):** `is_private_event` now catches `(Private)`, `[PRIVATE]`, `- private`, `Private BBQ` and other casual phrasings that used to slip through. New `test_is_private_event.py` at repo root locks the behaviour (18/18 pass). Smoke test against live calendar produced identical output to pre-fix, so no existing event changed classification. Also added the repo's first `.gitignore`. Closes the latent privacy-leak risk. See [bugs.md#b8](bugs.md).
- **B14 - Share promoted to primary CTA + button reorder + dark-mode CTA text fix (2026-04-18 midday):** Show-detail action row now reads `Share, Get Directions, Add to Calendar, All Shows`. Share is red-fill with white text, matches Get Directions and the nav BOOK THE BAND pill. Dark-mode black-text bug on `.btn-primary` fixed by hard-coding `color: #ffffff` instead of `var(--white)` (theme remaps `--white` to near-black). Also surfaced a pipeline gotcha: show-page template changes need both `build_show_pages.py` and `build_includes.py`, not just the first. Both lessons logged in bugs.md Fixed recently. See [bugs.md#b14](bugs.md).
- **R1 - Bandzoogle subscription cancelled (2026-04-18):** Ray closed the Bandzoogle account. Recurring subscription cost eliminated. Legacy-domain redirects to `/lander` were already in place via Cloudflare before cancellation; no infra change required on our side. See [roadmap.md#r1](roadmap.md).
- **B10 / B11 / B13 / B14-ish cleanup sprint (2026-04-18 AM):** B10 venue-duplication fixed in two passes (ingest-side in `sync_calendar.py`, render-side in `build_shows.py`). B10-follow-up `TX\b` regex tightened to not match `TX-276`. B11 breadcrumb now unique per show (`{venue} — {long_date}`). B13 red date badge squared up in two passes (72×72 then 80×80 after visual confirmation that child content was overflowing). B14 logged for next session (Share as primary CTA, reorder buttons). See [bugs.md](bugs.md) Fixed recently for details.
- **B2 / R8 / R10 - Regina as attendee, end-to-end (2026-04-17 PM):** Ray chose extend-the-webhook. `_updateEvent` and `_createEvent` in `docs/scripts/LiveRadioDFWCalendar.gs` now honor `attendees`/`guests` and return the resulting guest list. Deployed as Version 2 of the Apps Script, smoke-tested via `requests.post` against a throwaway event, torn down cleanly.
- **B3 - Outlook-native event IDs won't-fix (2026-04-17 PM):** Outlook calendar half of the old dual-entry pipeline formally decommissioned. New cardinal rule: band events created only on Google Calendar on info@. Existing Outlook-origin events remain hand-edit-only in the GCal UI but the population is finite and no longer growing.
- **B7 Part 1 - Passphrase rotated (2026-04-17 PM):** Old passphrase revoked, new passphrase lives in Ray's 1Password (`LiveRadioDFW Calendar webhook passphrase`) and in `gh-pages/sync_calendar.py`. End-to-end smoke test green. Part 2 still open — see #1 above.
- **B4 - Calendar host identity cleaned up (2026-04-17 PM):** Google Calendar owned by `info@liveradiodfw.com` (free Google personal account) is the confirmed source of truth. rmyers@futurebright.com is merely subscribed. 3 docs corrected, canonical statement added in `architecture/sources-of-truth.md`, master copy of the Apps Script committed to `docs/scripts/LiveRadioDFWCalendar.gs`, new runbook `runbooks/publish-calendar-webhook.md`. Spawned B7, J9, R10.
- **B5 - GitHub Pages challenge TXT:** restored in Cloudflare 2026-04-17 PM, verified on three resolvers.
- **CSS polish - square date badges on /shows:** `.show-card-full .show-date-badge` now renders 80x80 square, top-aligned to card (not stretched to full card height). Commit `4d3edc9` on `gh-pages`. Not logged as a bug since it was cosmetic refinement, not a defect.

## 📋 Pending discussion (not yet triaged into bugs or roadmap)

Things Ray has surfaced that need a Ray+Jarvis conversation before they become specific bug entries or roadmap items. Do NOT auto-action these - they are the input side of the prioritize / root-cause / discuss / solve workflow.

### D1. ChatGPT site audit findings (2026-04-17)
Ray ran a site audit through ChatGPT and it surfaced useful observations. Ray wants to discuss the findings with Jarvis before triaging them into specific bugs (defects) or roadmap items (enhancements). When this gets picked up:

- Ray pastes or summarizes the audit output
- Jarvis and Ray walk through each finding: is it a real defect, a nice-to-have, or noise?
- Real defects go to [bugs.md](bugs.md) with a B-prefix
- Enhancements go to [roadmap.md](roadmap.md) with an R-prefix
- Any that are noise or duplicates of existing items get explicitly noted and closed out

**Status:** Awaiting Ray to bring the findings into a session.

### D2. Use GitHub Issues / Projects / Wiki instead of markdown files? ~~[OPEN]~~ → **DECIDED 2026-04-18: keep markdown**

Ray asked whether to migrate bugs (B/J), roadmap (R), and decisions (D) from markdown files in `docs/` to GitHub Issues, and whether to adopt Projects and Wiki. Explored together 2026-04-18.

**Decision:** Keep the current markdown-file setup (`docs/bugs.md`, `docs/roadmap.md`, `docs/project-plan.md`). Do not migrate to Issues. Do not adopt Projects. Do not adopt Wiki.

**Why:**

- **Credit/tool-call cost:** A typical session today reads state in 1 file operation. With Issues, a typical session would be 3-4 API calls (list open issues + fetch 2-3 actively-worked issues). Full-archive reads would be ~16 calls vs. 1 today. That is a real, recurring per-session tax for marginal UI benefit given we are a two-actor team (Ray + Jarvis).
- **UI benefit is real but not painful-to-avoid:** Ray does not currently feel enough friction with the markdown flow to justify the migration cost. If that changes, we can revisit; the reverse migration is also roughly a 2-hour job.
- **Narrative fits prose better than tickets:** bugs.md carries rich multi-pass debugging stories (e.g., B14's three passes, B8's regex derivation), "How to add" templates, and a Lessons section. Issues handle discrete items well but fight long-form narrative. We would have to keep markdown for those pieces anyway, which means a hybrid system rather than a clean switch.
- **Wiki is a hard no regardless:** GitHub Wiki content lives in a separate git repo from the code. Our docs intentionally version alongside code in `docs/` so PRs touch both together. Decoupling would be a step backward.
- **Projects is a hard no today:** kanban value scales with number of actors. With one assignee (Ray) and one agent (Jarvis), Projects is ceremony without payoff. Revisit only if a third person joins the work.

**What we did adopt instead (from the same conversation):**

- Added `-marketing` sibling repo to the docs-read startup trigger (commit `660b511`).
- Filed R12 (end-to-end booking links in availability email), R13 (style guide audit), R14 (press-kit + why-book-us page enrichment).
- Added Section 11 to `MARKETING_STYLE_GUIDE.md` in `-marketing` as a guideline (not rule) for one primary CTA per venue-facing email, based on March 2026 send data (-marketing commit `71df18f`).

**Revisit triggers:**

- A third person joins the band-marketing work (contractor, band member, etc.) and needs assignee/kanban semantics.
- bugs.md crosses ~1500 lines and becomes genuinely unscannable.
- Ray feels real friction reading current state and asks for this again.

Until one of those triggers fires, do not re-open this discussion.

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

Linear list of open items has moved out of this file. See:

- **Live defects:** [bugs.md](bugs.md)
- **Planned work:** [roadmap.md](roadmap.md)

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
