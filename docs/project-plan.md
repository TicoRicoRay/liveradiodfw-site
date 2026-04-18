# Live Radio DFW — Project Plan

_Last updated: 2026-04-17 · 7:49 PM Central_

**This file is the session-to-session handoff.** For active defects see [bugs.md](bugs.md). For planned work see [roadmap.md](roadmap.md).


## 🚀 Starting a new session

Perplexity threads are disposable. This repo is the durable memory. To get a new agent up to speed fast, paste this as your first message:

> **Band marketing work on Live Radio DFW. Start the 60-min timer. Then: [today's task].**
>
> _Memory should carry: name (Jarvis), cardinal rules (EOS separation, Central not CDT/CST, no em-dashes, no "15 minutes" estimates, GCal source of truth for shows, Mailchimp for venue contacts, Cloudflare for DNS, `gh-pages` serves the site), and the docs-read trigger (on the phrase "Live Radio DFW" / "the band" / "band marketing", read https://github.com/TicoRicoRay/liveradiodfw-site/tree/docs - `docs/project-plan.md` first including "Pick up here next session", then `docs/bugs.md`, `docs/roadmap.md`, `docs/architecture/scheduled-tasks.md`, `docs/architecture/connectors.md` (which connectors are band-active vs. off-limits - critical because connectors are account-wide, not project-scoped), skim `docs/architecture/sources-of-truth.md` and `docs/runbooks/`, then the public site at https://www.liveradiodfw.com). Follow the "How to add" templates at the top of `bugs.md` / `roadmap.md` for any new bug or roadmap entry - no exceptions. "Wrap up" / "close out the thread" / "end of session" triggers the checklist at `docs/runbooks/end-of-session.md`._
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

**Context:** 2026-04-17 PM session was a foundation-building session, not a feature-building session. We split `project-plan.md` into three files (project-plan handoff / bugs / roadmap), hardened the "How to add" templates in `bugs.md` and `roadmap.md`, created `architecture/scheduled-tasks.md` as the durable cron inventory, logged J1-J8 (Jarvis's own blind spots) as bugs, logged B4 (calendar-host identity, deferred) and B6 (videos two-click), parked D1 (ChatGPT site audit), and closed B5 (GitHub Pages challenge TXT restored in Cloudflare).

**Heads-up for the NEXT thread specifically:** Ray is opening a fresh thread to stress-test whether the foundation work actually holds up on a cold start. Ray is trying a short startup prompt first ("Band marketing work on Live Radio DFW. Your name is Jarvis. My name is Ray. Start the 60-min timer. Read docs/ on the docs branch, then the public site. Cardinal rules apply. Then: [today's task].") — it leans on memory + this file's own embedded startup prompt to carry the cold agent. If the short prompt fails, Ray has three longer fallback versions stored in his notepad. Watch whether you (a) self-identify as Jarvis, (b) start the 60-min timer automatically, (c) read the docs before acting, (d) follow the "How to add" templates for any new bug/roadmap entry, and (e) remember the cardinal rules without being told (Central time, no em-dashes, never touch EOS calendar, GCal is source of truth for shows, Mailchimp for venue contacts, Cloudflare for DNS, no "15 minutes" estimates). If any of those fail, that is itself a bug worth logging as a new J-entry — and it means the short prompt isn't durable enough yet.

**Top priorities right now:**

1. **B7 - Part 2: move `sync_calendar.py` off `gh-pages`.** See [bugs.md#b7](bugs.md). Passphrase was rotated 2026-04-17 PM (Part 1), but the new value is still hard-coded in `gh-pages/sync_calendar.py` and therefore still fetchable at `https://www.liveradiodfw.com/sync_calendar.py` and GitHub raw. Relocate the sync script to a non-public host (likely Ray's Windows box; see B1) and read the passphrase from an env var or `.gitignore`d config file.
2. **B1 - DST-safe sync cron.** See [bugs.md#b1](bugs.md). Ray needs to find the owning thread in Perplexity's scheduled-tasks view. Naturally pairs with B7 Part 2 since both likely touch wherever the cron actually runs.
3. **D1 - ChatGPT site audit.** See "Pending discussion" below. Ray has audit findings to walk through before they become bugs or roadmap items.
4. **R1 - Cancel Bandzoogle.** See [roadmap.md#r1](roadmap.md). Legacy domains are already redirected; just needs Bandzoogle Domain Manager cleanup + cancellation.
5. **R4 - Wildcard 301s.** See [roadmap.md#r4](roadmap.md). Waiting on Search Console export from Ray.
6. **B6 - Videos two-click bug.** See [bugs.md#b6](bugs.md). Investigation-heavy; not a quick fix.

**Recently closed:**
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
