# Live Radio DFW — Project Plan

_Last updated: 2026-04-18 · 12:37 PM Central_

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

**Context:** 2026-04-18 session ran in two phases. Morning phase closed a bug+feature sprint (B8 private-event regex, B10 venue-dup follow-ups, B11 breadcrumb uniqueness, B13 date-badge squaring, B14 Share-as-CTA in three passes, R1 Bandzoogle cancellation) and generated durable artifacts (first test file in repo, first `.gitignore`). Midday phase was pure brainstorming - no bug/feature code, all direction-setting. Ray asked to explore cross-repo opportunities now that the `-marketing` sibling repo is in Jarvis's startup prompt; we filed three new roadmap items (R12 end-to-end booking links in availability email, R13 style guide vs site copy audit, R14 press-kit + why-book-us page enrichment), added Section 11 to `MARKETING_STYLE_GUIDE.md` in `-marketing` (one-primary-CTA guideline, not rule, dated Ray+Jarvis 2026-04-18), and closed one open question as D2 (keep markdown, don't migrate bugs/roadmap/decisions to GitHub Issues/Projects/Wiki). We also ran a 4-year retrospective on the monthly Mailchimp availability send and quantified the March 2026 rebuild: ~2x unique opens vs prior 8-send Live Radio baseline, 37.3% open rate vs 27.2% pooled prior, zero unsubscribes across 76 career sends. Confirmed the monthly cadence is not spammy by any reasonable measure - industry-beating on both opens and clicks, essentially zero churn. No code changes to `-site` or `-marketing` runtime paths this phase; all changes were docs / style guide.

**Heads-up for the NEXT thread specifically:** the three foundation items that were top priority coming into this session (B7 Part 2, B1, B6) are all still top priority - none of them got touched in either phase. The brainstorming phase filed forward-looking work (R12-R14) but did not take any of it on. New work should pick up on foundation, not on the new R-entries, unless Ray steers otherwise. Also worth noting: the startup prompt in this file now mentions the `-marketing` sibling repo explicitly (commit `660b511`), so a cold agent reading this block should have both repos in scope from turn one.

**Top priorities right now:**

1. **B7 - Part 2: move `sync_calendar.py` off `gh-pages`.** See [bugs.md#b7](bugs.md). Passphrase was rotated 2026-04-17 PM (Part 1), but the new value is still hard-coded in `gh-pages/sync_calendar.py` and therefore still fetchable at `https://www.liveradiodfw.com/sync_calendar.py` and GitHub raw. Relocate the sync script to a non-public host (likely Ray's Windows box; see B1) and read the passphrase from an env var or `.gitignore`d config file.
2. **B1 - DST-safe sync cron.** See [bugs.md#b1](bugs.md). Ray needs to find the owning thread in Perplexity's scheduled-tasks view. Naturally pairs with B7 Part 2 since both likely touch wherever the cron actually runs. Relevant new context: the real monthly availability cron lives in `-marketing`, not this repo - see `liveradiodfw-marketing/liveradiodfw_availability.py` and `setup_task_scheduler.ps1`.
3. **D1 - ChatGPT site audit.** See "Pending discussion" below. Ray has audit findings to walk through before they become bugs or roadmap items.
4. **R11 - head-level include extraction.** See [roadmap.md#r11](roadmap.md). High-leverage foundation item - makes future template-level fixes (like B12) single-file edits instead of 15-file sweeps. Ship before B12.
5. **R4 - Wildcard 301s.** See [roadmap.md#r4](roadmap.md). Waiting on Search Console export from Ray.
6. **B6 - Videos two-click bug.** See [bugs.md#b6](bugs.md). Investigation-heavy; not a quick fix.

**Recently closed:**
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
