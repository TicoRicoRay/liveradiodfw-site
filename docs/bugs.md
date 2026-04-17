# Live Radio DFW - Bug List

_Last updated: 2026-04-17_

Current known defects and correctness issues. Each bug lists symptom, where it manifests, workaround, fix options, and status.

This is the live bug list. Fixed bugs move to [postmortems/](postmortems/) or to the "Recently completed" section of [project-plan.md](project-plan.md).

For planned work that isn't a defect, see [roadmap.md](roadmap.md).

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

## B5. Missing `_github-pages-challenge-TicoRicoRay` TXT record

**Symptom:** The GitHub Pages domain-verification TXT record that was in the original DNS checklist is no longer present in Cloudflare. May have been dropped during the Cloudflare migration.

**Risk:** Low. GitHub could theoretically ask for re-verification later. Cloudflare proxy effectively prevents takeover in the meantime.

**Fix:** Pull fresh challenge value from `liveradiodfw-site` → Settings → Pages, add as TXT record in Cloudflare.

**Status:** Open, low urgency.

---

## Fixed recently (moved here for context; full history in postmortems)

- **2026-04-17 - Sync wipe:** `sync_calendar.py` was overwriting hand-curated fields in `shows.json`. Fixed with non-destructive merge + strict ticket-price parser. See [postmortems/2026-04-17-sync-wipe.md](postmortems/2026-04-17-sync-wipe.md).
- **2026-04-15 to 2026-04-16 - 12-hour outage:** during the Bandzoogle → Cloudflare → GitHub Pages migration. Fixed. See [postmortems/](postmortems/).
- **2026-04-17 - Silent "Free" default:** the ticket parser used to default to "Free" when no line was present. Now it alerts via email and leaves the field blank.
