# Live Radio DFW - Bug List

_Last updated: 2026-04-17_

Current known defects and correctness issues. Fixed bugs move to [postmortems/](postmortems/) or the "Recently completed" section of [project-plan.md](project-plan.md). For planned work that isn't a defect, see [roadmap.md](roadmap.md).

---

## How to add a bug (READ BEFORE ADDING)

All new bug entries must follow these rules. No exceptions - consistency is the whole point of this file.

### 1. Pick the correct prefix

| Prefix | Meaning |
|---|---|
| **B** | Band/system defect. Something about the site, sync, email, DNS, webhook, data, or any other non-AI part of the project is broken or wrong. |
| **J** | Jarvis (AI-agent) blind spot or tool limitation that affects this project. Use only when the defect is in how Jarvis or Perplexity operates. |

Planned work (enhancements, new features, migrations) does NOT go here. It goes to [roadmap.md](roadmap.md) with an **R** prefix. Items awaiting Ray+Jarvis discussion go to the "Pending discussion" section of [project-plan.md](project-plan.md) with a **D** prefix.

### 2. Pick the next sequential number

Scan the existing headings **and** find the highest number for that prefix. Add 1. Do not reuse numbers. Do not skip numbers. The B-series and J-series are numbered independently (B7 and J9 can coexist).

### 3. Use this entry template

```
## B<n>. <Short imperative title, no period>

**Symptom:** One or two sentences describing what's observed.

**Where:** Specific file(s), page(s), component(s), or system(s) where the bug manifests. Be precise.

**Impact:** What breaks for users, Ray, or operations. Why it matters.

**Workaround:** What to do today to avoid the bug, if anything. "None" is a valid answer.

**Fix options:** Proposed approaches, ordered from simplest to most invasive. Include trade-offs.

**Status:** Open / Decision-pending / Intentionally deferred / Fixed (<date>).
```

All six sections are required. Use "Unknown" or "TBD" if a field genuinely cannot be filled yet, but do not omit the field.

### 4. Commit message format

```
docs: log B<n> - <short title>
```

Example: `docs: log B7 - newsletter signup fails on iOS Safari`

### 5. After adding

- Commit to the `docs` branch
- Push
- Reply to Ray with the bug ID and commit link
- If the bug is top-priority, also update the "Top priorities right now" list in [project-plan.md](project-plan.md)

### 6. If in doubt, ask Ray

A half-complete bug entry is worse than no entry. If symptom or impact aren't clear, ask before writing.

---

## B1. Calendar sync cron drifts across DST

**Symptom:** Daily `sync_calendar.py` run fires at a fixed UTC minute (13:11 UTC), which lands at 8:11 AM Central in summer but 7:11 AM Central in winter. One-hour drift twice a year.

**Where:** Perplexity `schedule_cron` task owned by some prior thread (not visible from current threads via `schedule_cron(list)`).

**Workaround:** None - it just fires an hour early in winter.

**Fix:** Ray opens Perplexity's scheduled-tasks view in the app, finds the task (probably named "LiveRadioDFW calendar sync" or "daily sync"), notes the owning thread, then from that owning thread updates the schedule to a Central-aware cron expression. Document owning thread + task name in `architecture/calendar-sync.md` after the fix.

**Why not just recreate it here:** because each run costs Perplexity credits and we don't want two overlapping crons. Must update in place from the owning thread.

**Status:** Open. Top priority.

---

## B2. Webhook `attendees` field is a silent no-op

**Symptom:** Sending `attendees: ["falkor79@duck.com"]` to the Google Apps Script webhook's `update` action returns `status: updated` but does NOT actually add the attendee. Confirmed by Ray on OG Cellars 2026-04-18.

**Where:** Apps Script webhook (`Code.gs`). Blocks automated add of Regina (sound engineer) to future gig events.

**Workaround:** Add attendees manually in the Google Calendar UI.

**Fix options:**
- (a) Keep doing manual adds in GCal UI on each recurring/future event. Simplest, no code.
- (b) Extend `Code.gs` to honor `attendees` via `event.setAttendees([...])` or `event.addGuest(email)`, then add a post-sync step in `sync_calendar.py` to ensure Regina is on every future public event.

**Decision pending:** Ray to pick (a) or (b) before any code touches the webhook. Do NOT loop through events with the webhook until it's verified to honor `attendees`.

**Status:** Open, decision-gated.

---

## B3. Outlook-native event IDs can't be updated via the webhook

**Symptom:** Events created in Outlook that sync over to Google Calendar have an Outlook-native hex event ID (long hex string, no `@google.com` suffix). The Apps Script webhook's `update` action fails on these.

**Workaround:** Edit by hand in Google Calendar UI. Watters Creek 6/6 is a known example that required manual update.

**Fix:** Going forward, create events directly in Google Calendar to avoid generating Outlook-native IDs. Not clear whether existing Outlook-native events can be converted.

**Status:** Open, workaround documented.

---

## B4. Calendar host identity is ambiguous in docs

**Symptom:** The `docs` branch says the band calendar lives on `rmyers@futurebright.com` (in 4 places: `calendar-sync.md` x2, `sources-of-truth.md`, `edit-ticket-prices.md`, and a postmortem reference). Ray believes the real source of truth should be / is Outlook on the band's Microsoft 365 mailbox (`info@liveradiodfw.com`), not his personal Google account.

**Where:** `docs/architecture/calendar-sync.md` lines 8 and 31, `docs/architecture/sources-of-truth.md` line 7, `docs/runbooks/edit-ticket-prices.md` line 7, `docs/postmortems/2026-04-17-sync-wipe.md` line 60.

**Workaround:** None needed for day-to-day - sync still works because the webhook reads whichever Google Calendar it's wired to.

**Fix (deferred - rabbit hole):**
1. Confirm where the webhook is actually reading from (personal Google vs. band Google Workspace vs. Outlook via sync bridge).
2. Decide the canonical host. If it should be Outlook on `info@liveradiodfw.com`, design the bridge (e.g. Microsoft 365 → Google sync, or rewrite webhook against Microsoft Graph).
3. Rewrite all 4 doc locations in one pass.
4. Likely triggers cascading questions about the Outlook-native event ID bug (B3) and attendee bug (B2).

**Why deferred:** Every calendar change turns into a multi-hour rabbit hole. Don't touch until there's a dedicated session for it.

**Status:** Open, intentionally deferred.

---

## B6. Videos on site require two clicks to play

**Symptom:** Every embedded video on `liveradiodfw.com` requires two clicks to start playing. First click registers but does not initiate playback; second click plays the video.

**Where:** All video players on the live site. Exact file(s) and player component not yet identified in this thread.

**Impact:** Poor UX. Likely causes visitors to abandon before seeing video content. Affects fan engagement and booking-lead conversion.

**Prior work:** Worked on this in a prior thread; did not reach resolution. Details of what was tried are in that thread, not yet captured here.

**Likely causes to investigate:**
- Autoplay policy interaction: many browsers require a user gesture AND muted+inline attrs before programmatic `.play()` succeeds. A first click that triggers an unmuted `.play()` can fail silently, leaving the second click to hit the native control.
- Overlay / poster element intercepting the first click. Common pattern: a `<div>` poster layer covers the player, first click dismisses the overlay, second click actually hits the video element.
- Event handler attached to a wrapper that calls `.play()` on the video but something else (iOS/Safari gesture chain, CORS on the video source, a Promise rejection on `.play()`) blocks playback on the first gesture.
- Lazy-loaded `<iframe>` (e.g. YouTube embed) where first click triggers the iframe load and second click actually starts playback.

**Next steps:**
1. Identify which page(s) and which player component is used (native `<video>`, YouTube iframe, Vimeo embed, custom player)
2. Capture console output and Network tab on first click vs. second click in Chrome DevTools
3. Check for a poster/overlay element intercepting the first click
4. Open the prior thread (if locatable) to recover what was already tried, to avoid re-treading

**Status:** Open. Reproducible on live site. Priority TBD - nuisance level, not outage.

---

## B5. Missing `_github-pages-challenge-TicoRicoRay` TXT record

**Symptom:** The GitHub Pages domain-verification TXT record that was in the original DNS checklist is no longer present in Cloudflare. May have been dropped during the Cloudflare migration.

**Risk:** Low. GitHub could theoretically ask for re-verification later. Cloudflare proxy effectively prevents takeover in the meantime.

**Fix:** Pull fresh challenge value from `liveradiodfw-site` → Settings → Pages, add as TXT record in Cloudflare.

**Status:** Open, low urgency.

---

---

# Jarvis blind spots (AI-agent limitations that affect this project)

These aren't band bugs - they're limitations in how Jarvis (the AI assistant) can operate across threads. Logged here because they cause real band-work failures, so Ray and Jarvis can prioritize and address them the same way as any other defect. Mitigations live in the `docs` branch, startup prompt, and memory.

## J1. Scheduled tasks are invisible across threads

**Symptom:** `schedule_cron(list)` is thread-scoped. A task created in thread A is invisible from thread B, even to the same user. A future Jarvis cannot see or modify a cron set up by a prior Jarvis unless the owning thread is reopened.

**Impact:** This is the direct cause of bug B1. We spent ~2 hours on 2026-04-17 AM hunting for a daily sync that fires real credits we could not see from the active thread.

**Mitigation in place:** [architecture/scheduled-tasks.md](architecture/scheduled-tasks.md) is the durable inventory. New tasks must be documented there the same session they're created. Startup prompt tells new threads to read it.

**Residual risk:** Jarvis can still forget to log a new task before the session ends. Ray's pushback ("what scheduled tasks are running?") is the safety net.

**Status:** Open, mitigated.

## J2. Memory saves can silently soften wording

**Symptom:** When Jarvis calls `memory_update` with a strong directive (e.g. "ALWAYS start the timer"), the memory system sometimes saves a softer form ("sometimes asks for the timer") and sometimes drops phrases entirely. Confirmed live on 2026-04-17 during the work-session timer discussion.

**Impact:** Preferences and rules can quietly weaken across threads without Jarvis or Ray knowing.

**Mitigation:** After important memory saves, Jarvis reads the memory system's response to verify the save wording, and re-saves with stronger language if it was softened. Ray can ask "what did you save?" to audit.

**Status:** Open, mitigated but not solved. External limitation.

## J3. Perplexity Spaces cannot reach connectors

**Symptom:** Threads opened inside a Perplexity Space lack access to the external-tool connectors that normal threads have. Attempts to read the GitHub repo from inside a Space failed on 2026-04-17.

**Impact:** The otherwise-natural way to persist a project's system prompt (put it in the Space) doesn't work for LiveRadioDFW because the band-work startup requires reading the `docs` branch via the GitHub connector.

**Mitigation:** Do NOT use Spaces for band work. Instead: (a) Ray pastes a one-liner startup prompt from a desktop notepad, OR (b) memory trigger rule fires on the words "Live Radio DFW / the band / band marketing" and loads the docs.

**Status:** Open, external limitation. Design around it.

## J4. Memory is not guaranteed to load correctly in every thread

**Symptom:** A new thread should auto-load Ray's background, preferences, and project rules, but occasionally threads act amnesiac on specific facts.

**Impact:** Cardinal rules like "never read the EOS calendar" or "no em-dashes" or project separation can be silently missed by a fresh Jarvis until Ray notices and pushes back.

**Mitigation:** Triple redundancy - same rules in memory, in `docs/project-plan.md` rules of engagement, and in `docs/architecture/sources-of-truth.md`. The startup prompt forces a read of the project plan, so even memory-amnesiac threads pick up rules from the repo.

**Status:** Open, mitigated with redundancy.

## J5. `pause_and_wait` is the wrong tool for work-session timers

**Symptom:** `pause_and_wait` ends Jarvis's response and waits silently for the full duration. Using it for a 60-minute timer creates a 60-minute silence where Ray can't interact. Misused three times on 2026-04-17.

**Impact:** Broken conversation flow; Ray sees "Jarvis stopped responding" instead of working sessions.

**Mitigation:** Track timer state mentally (start + hard-stop timestamps), check the clock on every response, warn at 50 min and hard-stop at 60 min. Saved to memory as the correct approach.

**Status:** Fixed by behavior change. Left on the list as a reminder for future Jarvises.

## J6. Under pressure, Jarvis can theorize past contrary evidence

**Symptom:** On 2026-04-16 PM, Jarvis saw the `*.github.io` wildcard fallback cert on `www.liveradiodfw.com`, knew that GitHub uses it as a redirector fallback, and told Ray the live monitor was a false positive. Ray provided a browser screenshot proving the monitor right. Jarvis's theory ("the 301 redirect rescues the bad cert") ignored that TLS happens before HTTP.

**Impact:** Extended the outage by an entire afternoon and evening. Burned credits.

**Mitigation:** Postmortem lesson 6: "Trust the monitor, not your interpretation of 'it's fine.'" When evidence contradicts theory, evidence wins. Written into the postmortem and reinforced in the project-plan rules.

**Status:** Open behaviorally. Ray's pushback remains the primary safety net.

## J7. Jarvis can cross project boundaries under ambiguity

**Symptom:** Multiple times during band work, Jarvis searched the Gmail/GCal connector (which is EOS Worldwide, unrelated to the band) looking for band email, in violation of the clearly-stated rule.

**Impact:** Lost context, burned credits, risk of contaminating cardinal separation between projects.

**Mitigation:** Rule is now in memory, in `project-plan.md` rules of engagement, in `sources-of-truth.md` ("Never touch: the EOS calendar"), and in the startup prompt. Triple redundancy.

**Status:** Open behaviorally. External platform feature request: per-project connector allow-lists would solve this structurally.

## J8. Jarvis makes time estimates despite Ray's rule against it

**Symptom:** Jarvis has promised "15 minutes" at least once despite Ray's explicit pet peeve against it.

**Impact:** Sets wrong expectations, erodes trust.

**Mitigation:** Rule in memory ("never promise 15 minutes") and in `project-plan.md`. Jarvis simply does the work without estimating.

**Status:** Behavioral rule. Must re-surface at thread start.

---

## Fixed recently (moved here for context; full history in postmortems)

- **2026-04-17 - Sync wipe:** `sync_calendar.py` was overwriting hand-curated fields in `shows.json`. Fixed with non-destructive merge + strict ticket-price parser. See [postmortems/2026-04-17-sync-wipe.md](postmortems/2026-04-17-sync-wipe.md).
- **2026-04-15 to 2026-04-16 - 12-hour outage:** during the Bandzoogle → Cloudflare → GitHub Pages migration. Fixed. See [postmortems/](postmortems/).
- **2026-04-17 - Silent "Free" default:** the ticket parser used to default to "Free" when no line was present. Now it alerts via email and leaves the field blank.
