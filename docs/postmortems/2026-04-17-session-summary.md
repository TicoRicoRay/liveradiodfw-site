# Session Summary — 2026-04-17 (Live Radio DFW)

_Friday, April 17, 2026 · 7:00 AM – 12:00 PM Central_

## What we set out to do

The session started with a concrete ask: Google had cached `https://www.liveradiodfw.com/home`, so we needed a redirect plus a lander page for the Risky Business + Jackson Crossing → Live Radio DFW merger. Two strategy questions and an image URL came with it. Tactical and scoped.

It did not stay tactical.

## What actually happened

### 1. The lander + home-redirect (as planned)
Built `/lander.html` with the Bandzoogle merger announcement copy and a hero image (Risky Business + Jackson Crossing merging into Live Radio DFW). Added `/home.html` meta-refresh redirecting to `/` to recover the Google-cached URL. Live on `liveradiodfw.com` by mid-morning.

### 2. The OG Cellars incident
An automated email fired saying "OG Cellars ticket price was changed from $25 to Free." Ray pushed back: the calendar said $25. Investigation was where the day opened up.

- Agent initially looked in Outlook, found an empty description, and got confused.
- Ray sent screenshots from both Outlook AND Google Calendar showing "Tickets: $25" was present.
- Git history on `gh-pages` revealed the truth: the daily auto-sync at 13:11 UTC had **overwritten** the `shows.json` entry, silently defaulting ticket_price to "Free" when it couldn't parse the description — AND it had nuked the `description` field on the show entry entirely.
- Two bugs identified in `sync_calendar.py`:
  1. **Destructive sync** — every run did `current_shows[i] = new_show`, wiping any hand-curated fields (like `description`)
  2. **Silent parser default** — no `Tickets:` line meant "Free", with no alert

### 3. The fix (Option C, Ray's pick)
- Grandfathered `Tickets: Free` into Google Calendar descriptions for all 7 public non-OG-Cellars shows (via the webhook's `update` action)
- One event — Watters Creek 6/6 — has an Outlook-native hex event ID the webhook can't update. Ray fixed it by hand in the Google Calendar UI.
- Patched `sync_calendar.py`:
  - **Non-destructive merge** — sync only touches 12 "calendar-owned" fields, preserves everything else
  - **Strict parser** — missing ticket line = blank string + alert email, no silent defaults
- Dry-run confirmed: 10 shows, 10 events, **zero drift, zero alerts** on next run.

### 4. Documentation overhaul
Ray: "Dropbox is being a pain in the ass... what about GitHub for documentation?"

Created a `docs` orphan branch on `liveradiodfw-site`:
- `docs/project-plan.md` — open items + completed log
- `docs/runbooks/edit-ticket-prices.md` — daily ops
- `docs/runbooks/dns-and-pages.md` — rewritten from the stale `GITHUB_PAGES_CHECKLIST.md` in `-marketing` to match current Cloudflare→GH Pages architecture
- `docs/architecture/sources-of-truth.md` — calendar = shows, Mailchimp = venues, gh-pages = site, docs = this
- `docs/architecture/calendar-sync.md` — data flow + components
- `docs/architecture/marketing-automation.md` — the monthly availability-email automation
- `docs/postmortems/2026-04-17-sync-wipe.md` — migrated from workspace

Audited and fixed the `-marketing` repo:
- Removed stray `CNAME` (falsely implied that repo served the domain)
- Removed stale `GITHUB_PAGES_CHECKLIST.md` (said DNS was on GoDaddy — it's on Cloudflare)
- Rewrote `-marketing/README.md` to clarify repo roles and cross-link to the docs branch

### 5. The cron mystery (longest detour)
A GitHub identity `LiveRadioDFW <info@liveradiodfw.com>` commits auto-sync updates to `gh-pages` daily around 13:11 UTC. Nobody in this session created that schedule. Investigation went:

- First guess: "external machine Ray set up" (wrong — Ray said he didn't know how to write crons)
- Second guess: "GitHub Action" (wrong — verified via API, only `pages-build-deployment` runs)
- Third guess: "Ray's Windows box via Task Scheduler" (wrong)
- **Ray's clue that cracked it:** "every time it runs it costs me Perplexity credits"
- **Actual answer:** a Perplexity `schedule_cron` task created by a prior-session agent. Lives in whichever thread originally set it up. Invisible from this thread because `schedule_cron(list)` is thread-scoped.

Logged as open item #6 with action: Ray finds the task in Perplexity's scheduled tasks UI, we update from the owning thread to a Central-aware schedule so it doesn't drift an hour every November/March.

### 6. Timezone convention
Ray: *"Almost all events will be in Central. Does this simplify anything?"*

Answer: yes in one place — language. We're now using **"Central"** or **"America/Chicago"** everywhere, never CDT/CST. The DST-named variants cause silent off-by-an-hour bugs. Swept 6 doc files to remove CDT/CST.

### 7. Workflow realization
Ray, near the end: *"I'd like to keep everything together in a single thread. But I don't think Perplexity is up to the task."*

True, and we don't need to. The docs branch IS the persistent memory. Threads are disposable workers that read the docs, do a task, and update the docs. Added a "Starting a new session" prompt template at the top of `project-plan.md`.

## What we learned

### Architecture lessons

1. **Any sync process must be non-destructive by default.** Only touch fields you own. Preserve hand-curated data. Treat overwriting unknown fields as a bug, not a feature.
2. **Parsers must distinguish "missing" from "default".** "I couldn't parse a ticket price" is different from "the ticket price is Free". Silent defaults become silent data loss.
3. **Sources of truth must be named, not inferred.** We lost half an hour to "is the site driven by Outlook or Google?" before it was written down that Google is canonical.
4. **Tools that look stateful often aren't.** Perplexity memory forgets. `schedule_cron` is thread-scoped. Git is stateful. Use the stateful tool for state.

### Collaboration lessons

1. **When the agent's story doesn't match yours, trust yours.** Ray did this repeatedly today — the OG Cellars screenshot, the "I didn't write any cron" pushback — and each time it led to a real finding.
2. **Credits as a signal.** "It costs me credits" was the one-line clue that resolved the cron hunt. Cost and ownership are correlated in ways that narrow investigations fast.
3. **Language matters.** "Cron," "CDT," and "I wrote the cron" all caused confusion today. Using precise, DST-safe, mechanism-neutral vocabulary ("scheduled task," "Central") prevents it.

### Ray's rules (for future-me)

- **Not EOS.** Never read the EOS calendar for band work. Ever.
- **Foundation first.** Fix root cause before shipping new features.
- **We're doing surgery here.** Be precise. No guessing.
- **Never promise "15 minutes."** Don't estimate time; just do the work.
- **Coffee is a milestone.** Don't interrupt it with false positives.

## Outcomes

- Site live and clean. Zero calendar drift. Zero pending alerts.
- `sync_calendar.py` patched and deployed to `gh-pages` (commit `37c6f3e6`).
- Documentation centralized on the `docs` branch of `liveradiodfw-site`.
- `-marketing` repo cleaned up.
- Pick-up-next-session instructions at the top of `project-plan.md`.
- Open items: Bandzoogle domain migrations, wildcard 301s, historic shows migration, GSC cleanup, **cron DST fix**, timezone convention adopted.

## Next session starts here

Paste this as the first message:

> Band marketing work on Live Radio DFW. Before anything else, read https://github.com/TicoRicoRay/liveradiodfw-site/tree/docs — start with `docs/project-plan.md` (especially "Pick up here next session"), then skim `docs/architecture/sources-of-truth.md` and `docs/runbooks/`. Then [today's task].

---

_Session ended clean at 12:00 PM Central by Ray's hard stop._
