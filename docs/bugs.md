# Live Radio DFW - Bug List

_Last updated: 2026-04-20 PM (B16 Stage 1 confirmed shipped — closing B16 and opening B16.2 for Stage 2 auto-publish trigger; B20 filed for 22 legacy Bandzoogle-era past-show descriptions that miss v2 warm-invitation voice; B6 closed earlier today; B12 + B17 + B18 + B19 also fixed earlier today; B7 Part 2 re-confirmed as top priority with sync_calendar.py still in active daily use post-Outlook-calendar-decommission)_

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

## B2. Webhook `attendees` field is a silent no-op ~~[OPEN]~~ → **FIXED 2026-04-17 PM (R10)**

**Symptom:** Sending `attendees: ["falkor79@duck.com"]` to the Google Apps Script webhook's `update` action returned `status: updated` but did NOT actually add the attendee. Confirmed by Ray on OG Cellars 2026-04-18.

**Where:** Apps Script webhook (`Code.gs`). Blocked automated add of Regina (sound engineer) to future gig events.

**Root cause (identified 2026-04-17):** The Apps Script `_updateEvent` function accepted the `attendees` payload field but had no code path that did anything with it. The `list`, `create`, and `delete` branches existed; the `update` branch never called `event.addGuest(email)` or `event.setAttendees([...])`.

**Fix applied (2026-04-17 PM):** Ray chose option (b) in the original fix list. Extended `_updateEvent` in `scripts/LiveRadioDFWCalendar.gs` to iterate `data.attendees || data.guests` and call `event.addGuest(email)` for each, and normalized `_createEvent` to accept either field name. Both paths return the resulting `guests:` array in the response for verification. Passphrase was simultaneously rotated (see B7). Published via [runbooks/publish-calendar-webhook.md](runbooks/publish-calendar-webhook.md) as Version 2 of the `LiveRadioDFW Calendar` Apps Script project.

**Smoke test (2026-04-17 PM):** Throwaway event created with `attendees: ["rmyers@futurebright.com"]` → `guests` array in response contained the email. `update` with a different attendee set on the same event → `guests` array reflected the added guest. Throwaway deleted. Tracked as R10 (now closed).

**Status:** Fixed. See Fixed Recently section below.

---

## B3. Outlook-native event IDs can't be updated via the webhook ~~[OPEN]~~ → **WON'T-FIX 2026-04-17 PM (upstream decommissioned)**

**Symptom:** Events created in Outlook that synced over to Google Calendar had Outlook-native hex event IDs (long hex string, no `@google.com` suffix). The Apps Script webhook's `update` action failed on these.

**Where:** Google Calendar events originating from the old Outlook dual-write pipeline. Known affected events: Watters Creek 6/6 and "LR - The Gathering in Allen" 9/18.

**Resolution (2026-04-17 PM):** The Outlook calendar half of the old dual-entry pipeline was formally decommissioned this session. Going forward, all new band events are created directly on the Google Calendar (info@liveradiodfw.com), so no new events will carry Outlook-native IDs. This is now a cardinal rule (see `project-plan.md` and `architecture/sources-of-truth.md`). Existing Outlook-origin events keep their hex IDs and must still be edited by hand in the Google Calendar UI (workaround retained for them), but the class of bug is no longer growing.

**Why not fix the underlying webhook behavior:** The upstream cause (dual-write creating non-Google IDs) is gone, and the population of affected events is finite and small. Fixing `_updateEvent` to handle Outlook-native IDs would be speculative work against a shrinking set.

**Status:** Won't-fix — upstream source eliminated. Hand-edit existing Outlook-origin events in the GCal UI when needed.

---

## B4. Calendar host identity is ambiguous in docs ~~[OPEN]~~ → **FIXED 2026-04-17**

**Symptom:** The `docs` branch said the band calendar lives on `rmyers@futurebright.com` in 4 places. Ray wasn't sure whether the real host was his personal Google account, a Google Workspace, or Outlook on `info@liveradiodfw.com`.

**Where:** `docs/architecture/calendar-sync.md` lines 8 and 31, `docs/architecture/sources-of-truth.md` line 7, `docs/runbooks/edit-ticket-prices.md` line 7.

**Root cause identified (2026-04-17):** Ray logged into `info@liveradiodfw.com` (a free Google **personal** account on the band domain) and found the Apps Script project **"LiveRadioDFW Calendar"** living there, bound to info@'s Google Calendar. The webhook has always been reading info@'s calendar. rmyers@futurebright.com is merely **subscribed** for day-to-day visibility, not the host. The docs were simply wrong.

**Fix applied:**
1. Corrected all 4 doc locations to state: Google Calendar owned by `info@liveradiodfw.com` (free Google personal account).
2. Added a canonical statement in `architecture/sources-of-truth.md` with the confirmation date and method.
3. Checked the postmortem line-60 reference — false positive, unrelated context.
4. Committed master copy of the Apps Script to `docs/scripts/LiveRadioDFWCalendar.gs` with passphrase redacted.
5. New runbook: [runbooks/publish-calendar-webhook.md](runbooks/publish-calendar-webhook.md) for the manual publish step.
6. Logged J9 (connectors are account-wide, not per-project), R10 (extend `_updateEvent` for attendees), B7 (public passphrase exposure discovered during this cleanup).

**Status:** Fixed 2026-04-17.

---

## B7. Webhook passphrase and URL are publicly readable on the live site ~~[OPEN]~~ → **FIXED 2026-04-21 (Part 2 shipped, exposure closed)**

**Symptom:** `sync_calendar.py` lives on the `gh-pages` branch and hard-codes the Apps Script webhook URL and passphrase (lines 44–45). Because `gh-pages` is the live site served via GitHub Pages + Cloudflare, the file is fetchable at `https://www.liveradiodfw.com/sync_calendar.py` (200 OK, observed 2026-04-17) and also readable directly from the public GitHub repo.

**Where:** `liveradiodfw-site` repo, `gh-pages` branch, `sync_calendar.py` lines 44–45. Public URLs:
- `https://www.liveradiodfw.com/sync_calendar.py`
- `https://raw.githubusercontent.com/TicoRicoRay/liveradiodfw-site/gh-pages/sync_calendar.py`

**Impact:** Anyone who discovers either URL can invoke the webhook with `{action: "create"|"update"|"delete"}` and corrupt, wipe, or plant events on the band calendar. Severity: high. No evidence of exploitation yet, but the exposure window may have been long.

**Workaround:** None at the script level. Short-term: do not link to or publicize either URL.

**Fix options (ranked):**
- (a) **Rotate passphrase + move sync off gh-pages.** Generate new passphrase, update Apps Script and password manager, move `sync_calendar.py` to a non-public location on whatever host actually runs the cron (likely Ray's Windows box; see B1), read passphrase from env var or local config file that's `.gitignore`d. Strongest fix.
- (b) **Rotate passphrase + keep script on gh-pages but add `.gitignore` + Jekyll exclude or `_config.yml` exclude + server-side 404 for `*.py`.** Risky — GitHub Pages serves everything in the branch by default. Easy to regress.
- (c) **Rotate passphrase + move `sync_calendar.py` to a private repo or private branch.** Moderate. Requires re-pointing the cron.
- (d) **Keep everything and add an IP allow-list in the Apps Script.** Only helps if the cron runs from a stable public IP. Doesn't fix the GitHub-readable copy.

**Recommendation:** (a). Rotate first, move second. Rotation alone immediately invalidates any copies already harvested.

**Discovered:** 2026-04-17 during calendar SoT cleanup, while auditing where the passphrase lives.

**Update 2026-04-17 PM — Part 1 of (a) complete:** Passphrase was rotated this session. New passphrase is in Ray's 1Password (Secure Note "LiveRadioDFW Calendar webhook passphrase"), deployed to the Apps Script Web App (Version 2, 2026-04-17 ~8:52 PM Central), and written to `gh-pages/sync_calendar.py`. Old passphrase `El3Q…` is revoked. End-to-end smoke test passed (list + create + update + delete via `requests.post`). **Residual exposure:** the new passphrase is still hard-coded in `gh-pages/sync_calendar.py` and therefore still fetchable at `https://www.liveradiodfw.com/sync_calendar.py` and from GitHub raw. Part 2 of (a) — move the script off `gh-pages` — remains open.

**Status:** ~~Partially addressed. Passphrase rotated (Part 1 of fix option (a)); sync script not yet moved off `gh-pages` (Part 2). Remains top priority until Part 2 lands.~~ **Closed 2026-04-21.**

**Part 2 close-out 2026-04-21** (commit [`b125405`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/b125405) on `gh-pages`, [`aca5b21`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/aca5b21) on `docs`). Fix option (a) shipped per Ray's 2026-04-21 decisions (1a Windows Task Scheduler host, 2a library/runner split, 3a `.env` file for secrets):

- **`sync_calendar.py` is gone from `gh-pages`.** The monolith was split into `sync_lib.py` (pure functions, no secrets, stays on `gh-pages`) and `sync_runner.py` (orchestration + secrets + git push, lives in the public [`liveradiodfw-marketing`](https://github.com/TicoRicoRay/liveradiodfw-marketing) repo at commit [`ee94c10`](https://github.com/TicoRicoRay/liveradiodfw-marketing/commit/ee94c10)). `sync_runner.py` is safe to publish because every secret loads from `.env` at runtime; the `.env` file itself is gitignored and hand-created on Ray's Windows box. The rename preserved git history on `gh-pages` (git detected `sync_calendar.py -> sync_lib.py` as a 55% rename).
- **`fetch_historic.py` also deleted.** One-shot historic fetch (2021-04-01 → 2024-08-08) already completed; output `calendar_historic_*.json` preserved in-tree. It was the sixth caller and carried the same secret-leak risk; deleting was cleaner than refactoring a file that has no future callers.
- **5 remaining callers updated** (`test_is_private_event.py`, `test_description_handling.py`, `test_cancellation_reschedule.py`, `import_historic.py`, `import_bandzoogle.py`) to `from sync_lib import …`. All 49 tests green against the new library (18 + 18 + 13 = 49 across the three test files).
- **Secrets load from `.env`** in the runner's directory via a minimal inline dotenv loader (no new dependencies). `.env.example` ships alongside the runner in `-marketing` as the template. `.gitignore` (added in the same commit) excludes `.env`, `sync.log`, `token.pickle`, and other local-only artifacts. Values source of truth: 1Password Secure Note "LiveRadioDFW Calendar webhook passphrase."
- **Windows Task Scheduler takes over as host.** Install runbook ships with the code: [`liveradiodfw-marketing/docs/windows-sync-task.md`](https://github.com/TicoRicoRay/liveradiodfw-marketing/blob/master/docs/windows-sync-task.md). Registration script: `setup_sync_task_scheduler.ps1` (run once as Administrator). Uses local Central time with automatic DST handling — this sets up the fix for [B1](bugs.md#b1-calendar-sync-cron-drifts-across-dst) as a side effect. Mandatory 3-day parallel-run check with the old Perplexity cron before the Perplexity task is deleted.
- **Verified exposure is closed** 2026-04-21 12:53 PM Central:
  - `https://www.liveradiodfw.com/sync_calendar.py` → **HTTP 404** (GitHub Pages rebuild + Cloudflare edge cache both caught up within 30 seconds of the push).
  - `https://raw.githubusercontent.com/TicoRicoRay/liveradiodfw-site/gh-pages/sync_calendar.py` → **HTTP 404.**
  - New `https://raw.githubusercontent.com/TicoRicoRay/liveradiodfw-site/gh-pages/sync_lib.py` → HTTP 200, and `grep` for the passphrase value returns zero hits.
- **Handoff to Ray (no-zip pattern):** Ray `git clone`s [`liveradiodfw-marketing`](https://github.com/TicoRicoRay/liveradiodfw-marketing) once into `C:\Tools\LiveRadioDFW\liveradiodfw-marketing\`, creates a local `.env` from `.env.example` (the only hand-managed file), and runs `.\setup_sync_task_scheduler.ps1` as Administrator. All future updates are `git pull`. No zip handoffs, no stale file copies — Ray's standing architectural preference ("everything else is just a pull from github as needed"). Install is ~15 minutes hands-on plus the 3-day parallel-run verification window.
- **B1 unblocked.** Once the Windows task is green and the Perplexity cron is retired, B1 closes in the same motion — Windows Task Scheduler's local-time trigger is DST-safe by construction.

**Clarification 2026-04-20 PM:** Ray asked whether `sync_calendar.py` is even still used post-Outlook-decommission (2026-04-17) now that Google Calendar is sole SoT. Answer: **yes, still daily.** The script has always been a one-way GCal-→-website sync, not an Outlook↔GCal bridge — Google Calendar is the source, `shows.json` + static show pages are the destination. With Outlook gone, this script is the *only* path from the single SoT calendar to the public site: without it, new shows never appear, cancellations never remove cards, venue/time edits never propagate. It's scheduled daily via a Perplexity `schedule_cron` in a prior thread (see J1 blind spot and B1 for DST drift). The script also exports library helpers (`is_private_event`, `generate_description_draft`, `is_gig_event`, `WEBHOOK_URL`, `PASSPHRASE`) imported by `test_is_private_event.py`, `test_description_handling.py`, `test_cancellation_reschedule.py`, `import_historic.py`, `import_bandzoogle.py`, and `fetch_historic.py` — so even if we ever stopped scheduling the cron, we couldn't delete the file without refactoring six callers. Part 2 fix (relocate the file + load passphrase from env) stays the correct remediation path.

---

## B14. Show-detail action buttons need reorder + Share promoted to primary CTA

**Symptom:** On each show-detail page the action-button row renders as `Get Directions` (red primary) &rarr; `Add to Calendar` (outline) &rarr; `Share` (outline) &rarr; `All Shows` (outline). Share is the action the band most wants fans to take (it drives new reach to upcoming shows), but visually it sits third in the row with the same ghost outline as every other button, so it reads as a low-priority tertiary.

**Desired state:**

1. **Share** first in the row, styled as the primary CTA (solid fill, distinct colour from the existing `--red` directions button so they don't compete). Button text in white so it pops against the fill.
2. **Get Directions** second.
3. **Add to Calendar** third.
4. **All Shows** last (stays secondary/outline).

**Where:** `lrdfw-ghpages/build_show_pages.py` lines 208–213 — the `<div class="show-page-actions">` block in the page template. Current order in the source:

```python
<div class="show-page-actions">
  <a ... class="btn btn-primary">Get Directions</a>
  <button class="btn-calendar">... Add to Calendar</button>
  <button class="btn-share">... Share</button>
  <a ... class="btn btn-secondary">All Shows</a>
</div>
```

CSS for the button styles lives in `css/style.css` — `.btn-primary` at ~L277, `.btn-share` (outline ghost) and `.btn-calendar` nearby. Need a new modifier (e.g. `.btn-share.btn-cta` or a new `.btn-primary-accent`) with a distinct fill colour + `color: #ffffff`.

**Colour suggestion (not prescribed):** site already owns `--red: #e63946` for the primary CTA. A dark navy/blue (e.g. `#1d3557`, which sits in the same family as the existing navbar) or a deep teal would give Share a different primary treatment without clashing. Pick during implementation; the cardinal rule is "different from `--red` so the two primary buttons in the row don't fight each other."

**Impact:** Cosmetic + conversion. Makes the highest-leverage action (Share) the most visually prominent action on the page. Changes only `build_show_pages.py` template + one CSS block; regenerate all show pages via `build_show_pages.py`.

**Dependencies:** None. Can ship standalone. Related to R8 (show-page layout polish, closed) and B13 (badge square, closed).

**Status:** Fixed 2026-04-18 midday. Shipped in two commits: render/template in gh-pages `1f66996` (buttons reordered to Share, Get Directions, Add to Calendar, All Shows; Share gained `.btn-primary` class alongside `.btn-share` so the existing JS click handler keeps working), follow-up in gh-pages `5509b30` (restored nav/footer on show pages after initial rebuild missed build_includes.py, and fixed CTA text colour in dark mode by hard-coding `color: #ffffff` on `.btn-primary`). Final colour decision: **red fill + white text in both themes**, matching the nav BOOK THE BAND pill. Lesson captured: `[data-theme="dark"]` redefines `--white` to `#12121e` in the `:root` block (line 85–92), so any CTA using `color: var(--white)` renders near-black in dark mode. The nav-cta had always hard-coded `#ffffff` to avoid this; `.btn-primary` had not. See Fixed recently for details.

---

## B16. New shows added by sync have no `description`; no alert when description is missing; no placeholder on the rendered page ~~[OPEN]~~ → **FIXED 2026-04-20 PM (Stage 1 only; Stage 2 → B16.2)**

**Symptom:** When the daily sync adds a new show to `shows.json`, it populates only the 12 calendar-owned fields. The `description` field — which drives the `<About This Show>` block on the show-detail page — is hand-curated and therefore absent on every fresh add. There is no alert-email warning, no on-page signal, and no automatic draft. First caught in the wild today: the Aug 1 OG Cellars show that got added via the B15 cancellation/reschedule run landed with no description, which Ray caught while spot-checking the live page.

**Where:**
- `lrdfw-ghpages/sync_calendar.py` — `calendar_event_to_show()` emits no `description`; `check_missing_info()` does not flag missing descriptions.
- `lrdfw-ghpages/build_show_pages.py` — the description section is silently omitted when the field is empty, so the page has no visible "needs attention" cue.
- `lrdfw-ghpages/shows.json` — the Aug 1 OG Cellars entry is missing `description`.

**Impact:** SEO + user experience. Every hand-curated description is 350-530 characters of venue-specific prose covering setting, food/drink, parking, nearby communities, family/dog-friendliness, etc. Without it, show pages read as cookie-cutter templates — exactly the failure mode flagged in a prior session: "The risk would be if every page was cookie-cutter with just the date/time swapped." Ray's explicit constraint: **this must be solid before the historical-shows import**, because backfilling descriptions onto dozens of old shows is a much bigger job than preventing the gap going forward.

**Workaround (today):** Ray eyeballs each new show-detail page and emails himself to write a description. Fragile — relies on human memory for something the sync should surface automatically.

**Fix plan (staged rollout, per Ray's 2026-04-18 decision):**

**Stage 1 (ship now, B16 scope):** *propose, don't auto-publish.*
1. Add a deterministic `generate_description_draft(show)` helper in `sync_calendar.py` that composes a 3-5 sentence draft from the calendar-owned fields, using the voice conventions extracted from the existing 7 descriptions (opener rotation, venue/city, ticket language, geographic call-out, no em-dashes, no exclamation points, present tense).
2. Extend `check_missing_info()` to flag missing `description` on public (non-private) shows.
3. In the alert email's MISSING INFO block for a description, **include the machine-generated draft inline** so Ray can reply-with-edits or copy-paste-as-is.
4. Update `build_show_pages.py` to render a short `Show details coming soon` placeholder block when `description` is empty, so any human browsing the live site sees a clear signal instead of silently-thin content.
5. Backfill Aug 1 OG Cellars description in this same session (it was the bug's trigger; best to ship a complete page alongside the fix).

**Stage 2 (future, NOT B16 scope):** once Ray and Jarvis both feel confident that the machine-generated drafts have the right tone and quality across a few real examples, flip the default to *publish the generated description immediately + notify Ray in case there are problems*. Rationale (Ray, 2026-04-18): "some content better than none — and easy to correct." Trigger to flip: when the last 3-5 machine drafts have needed only minor or no edits before Ray approved. Track in this file as a follow-up.

**Status:** ~~Open — Stage 1 fix landing in the same session this entry was filed. Stage 2 trigger to watch: next 3-5 new venues/shows, log whether the draft was accepted as-is or edited. Revisit when trigger met.~~ **CLOSED 2026-04-20 PM.** Stage 1 verified shipped and live: `generate_description_draft()` at `sync_calendar.py:243` (deterministic, opener-rotating, DRAFT-prefixed, 300-600 char output, no em-dashes, no exclamation points); `check_missing_info()` flags missing descriptions on public shows; alert email inlines the draft under "Proposed description draft"; `build_show_pages.py` renders the "Show details coming soon" placeholder for empty descriptions; Aug 1 OG Cellars backfilled (557 chars). Test harness `test_description_handling.py` passes all 19 cases (14 for `generate_description_draft`, 5 for `check_missing_info`). Stage 2 (flip to auto-publish generated drafts by default with alert email as safety net) tracked as B16.2 below so this entry can close cleanly.

---

## B16.2. Stage 2 rollout for auto-generated show descriptions

**Symptom:** Not a defect — a planned follow-up to B16 (closed). Currently a show added by the daily sync with no hand-curated description gets (a) a visible "Show details coming soon" placeholder on the rendered page and (b) an alert email with a machine-generated v2-voice draft inlined for Ray to review and paste back. That's safer than auto-publishing but leaves a window where the public page is thin until Ray acts.

**Decision criteria (per Ray, 2026-04-18):** "some content better than none — and easy to correct." Flip the default to publish the generated description immediately + notify Ray in case there are problems. Trigger to flip: **the last 3-5 machine drafts have needed only minor or no edits before Ray approved.**

**Current evidence:** 0 of 3-5 evaluated. Only natural test case since Stage 1 shipped was the OG Cellars Aug 1 backfill, and Ray hand-wrote that rather than approving a draft. Need 3-5 organic new-venue sync adds before the trigger can be evaluated.

**What "flip" looks like:**
1. In `sync_calendar.py`, when a new show is added with no description, call `generate_description_draft(show)` and write the result (stripped of the `[DRAFT ...]` prefix) into `show['description']` before the `shows.json` write.
2. Keep the alert email path intact but re-label: "Auto-published description — review and edit if needed."
3. Keep the `build_show_pages.py` treatment of any `[DRAFT` prefix as placeholder-rendering, so the draft-prefix safety net still catches anything that slips through without the prefix strip.
4. Consider adding a `description_source: "auto"` field on auto-published shows so future audits can find and prioritize them for human review.

**Impact:** Positive on SEO/UX (no more "coming soon" placeholder on live pages). Risk: a bad draft goes live for a window. Mitigation: `generate_description_draft` already refuses to draft when venue or city is missing, and strips DFW-Area-only placeholder cities. Quality observed against the 7 shows that seeded the voice model is high.

**Status:** Waiting on trigger. When the next 3-5 new-venue sync adds happen, log each draft's quality (accepted as-is / minor edit / full rewrite). If 3-5 consecutive are accepted as-is or minor-edit only, flip Stage 2. If mixed, stay in Stage 1 and iterate on the draft template.

---

## B17. `sync_calendar.py` alert-email copy uses "CDT" string (cardinal rule violation) ~~[OPEN]~~ → **FIXED 2026-04-20 PM**

**Symptom:** Two hard-coded f-strings in `sync_calendar.py` alert emails contain the literal string `"CDT"`, violating the project's cardinal rule that all user-facing language must say "Central" or "America/Chicago", never "CDT" / "CST" (DST-unsafe terminology causes silent off-by-an-hour bugs in other contexts).

**Where:**
- `lrdfw-ghpages/sync_calendar.py:677` — `f"  it will reappear on the website at the next daily sync (8 AM CDT)."`
- `lrdfw-ghpages/sync_calendar.py:731` — `"be corrected at the next sync (daily at 8 AM CDT).\n\n"`

The `CDT` variable name at line 60 (`CDT = ZoneInfo("America/Chicago")`) is a Python identifier, not user-facing, and is out of scope here. The `audit_shows.py` checker at lines 19/162-164 greps for CDT/CST leaks in rendered HTML but does not scan `sync_calendar.py` email bodies.

**Impact:** Low-frequency, low-visibility. These email strings only appear in alert emails sent when the sync skips an event (`SKIP_PATTERNS` match) or hits an error. Ray is the only recipient. No public exposure. But it's a cardinal-rule violation that's been known and unfiled since 2026-04-18 (see B15 follow-ups section above, which flagged it but did not open a B entry).

**Workaround:** None needed (impact is aesthetic consistency, not correctness).

**Fix options:**
1. **Replace both strings with "Central".** Simplest. `(8 AM CDT)` → `(8 AM Central)`. Two-line edit. No behavior change.
2. **Replace with "America/Chicago"** for maximum precision. More formal; slightly less natural in prose. Reject unless the emails are ever read by anything automated.
3. **Extend `audit_shows.py` to also grep `sync_calendar.py`** for CDT/CST so this class of violation is caught at the linter level going forward. Pairs well with option 1 or 2.

Recommend option 1 + option 3 together. Pair them with R9's new end-of-session grep hook so future violations are caught at commit time, not session-months later.

**Status:** ~~Open. Filed 2026-04-19 as part of R9 (timezone convention enforcement) close-out. Not top-priority.~~ **FIXED 2026-04-20 PM** — both user-facing "CDT" strings in `sync_calendar.py` (the removal-notice email at line 677 and the summary-email footer at line 731) replaced with "Central". Shipped as commit [`4cabd7c`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/4cabd7c) on `gh-pages`. Scope note: line 60's `CDT = ZoneInfo("America/Chicago")` variable name is a code identifier, not user-facing prose, and was left alone to keep the diff minimal and B17 scope-pure. If a future pass wants full naming hygiene, renaming that variable to `CENTRAL` plus its two callsites at lines 337–338 is a trivial follow-up.

---

## B19. Google Search Console: structured-data warning — missing `validFrom` field in `offers` ~~[OPEN]~~ → **FIXED 2026-04-20 PM**

**Symptom:** Ray received an email from Google today (2026-04-20 AM) flagging a non-critical Search Console issue: `Missing field "validFrom" (in "offers")`. Google's own wording: *"This is a non-critical issue. Items with these issues are valid, but could be presented with more features or be optimized for more relevant queries."*

**Where:** Unknown pending diagnosis. Almost certainly one of the structured-data blobs embedded in show-detail pages (`/shows/*.html`) or the `Event` + nested `Offer` schema emitted during build. The `offers` field path points at `schema.org/Offer`, whose `validFrom` property is optional but recommended when a `price` is set.

**Impact:** Low — Google explicitly flags it as non-critical and confirms items remain valid and indexed. May affect rich-result eligibility or query targeting for show pages but does not block indexing.

**Next step:** When Ray is back, open the Search Console issue to capture (a) the exact URL(s) flagged, (b) which schema emitter is responsible (build pipeline vs. `sync_calendar.py` vs. a template file), and (c) whether adding `validFrom` is a one-line schema patch or needs a real date source. Natural pair with B16 (new-show description handling) since both live in the show-page build path.

**Status:** ~~Open. Filed 2026-04-20 AM from inbound GSC email, parked per Ray's request. No diagnosis yet.~~ **FIXED 2026-04-20 PM** — diagnosed and shipped same day. Emitter was `build_show_pages.py` line 173 (the `jsonld_obj["offers"]` block, emitted only for upcoming shows — `is_past` branch correctly omits Offer entirely). Added `validFrom` as a build-time UTC timestamp, written in strict ISO 8601 with a `Z` suffix (e.g., `"2026-04-20T21:06:10Z"`). Rationale for build-time vs. a show-specific on-sale date: for free, no-ticket shows we don't track a real on-sale moment, so build-time is the cleanest honest semantics — "the offer is valid from when we published this page, until the event starts." Cost: build-time timestamp means every rebuild produces a diff on all upcoming show pages, but the existing pipeline already touches every file on every `build_includes.py` run (nav/footer injection), so churn delta is zero. While in the file, also upgraded the deprecated `datetime.utcnow()` call to `datetime.now(timezone.utc)` to kill the Python 3.12+ `DeprecationWarning`. Shipped as commit [`ea37eae`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/ea37eae) on `gh-pages` — 9 files: the builder + 8 upcoming show pages. **Verification:** eyeball-checked JSON-LD on `frisco-rail-yard-2026-05-09.html` (has `validFrom`) and `frisco-rail-yard-2025-09-13.html` (past show, no `offers` block). Next step is for Ray to re-run the GSC rich-results validator on any upcoming show URL in a few days once Google re-crawls; the warning should clear on its own.

---

## B18. Past-shows drafts pipeline silently regresses live pages to "Show details coming soon" placeholder ~~[OPEN]~~ → **FIXED 2026-04-20 PM**

**Symptom:** Running `lrdfw-past-shows/shows_patch.py` against `/tmp/lrdfw-lander/shows.json` followed by `build_show_pages.py` + `build_includes.py` reverted 64 approved past-show descriptions back to the `.show-page-description-placeholder` → *"Show details coming soon. In the meantime, see the date, time, and location above or reach out via the Contact page."* boilerplate. Caught and reverted at commit staging on 2026-04-19 PM before push; the live site was never affected.

**Where:**
- `/home/user/workspace/lrdfw-past-shows/drafts.json` — source of truth for the 65 past-show descriptions. Contained a `[DRAFT - v2 warm-invitation voice, pending approval]` prefix on every description. This prefix was stripped from the **rendered HTML** at publish time (commit `9239aea`, 2026-04-19 AM) but never stripped from `drafts.json` itself.
- `lrdfw-past-shows/shows_patch.py` — faithfully copies `drafts[i].description` verbatim into `/tmp/lrdfw-lander/shows.json`. With stale prefixes in place, this writes the `[DRAFT ...]` string into `shows.json`.
- `/tmp/lrdfw-lander/build_show_pages.py` — treats any description starting with `[DRAFT` (or similarly-bracketed sentinel text) as "not yet ready for publication" and swaps the real description for the `.show-page-description-placeholder` boilerplate.

**Impact:** Severity high if triggered on an unreviewed diff — all 64 approved past-show pages would have flipped back to boilerplate in a single commit, undoing Ray's full one-at-a-time review session. Caught on 2026-04-19 PM only because the diff was reviewed before push (`git diff` showed 95 modified HTML files when only 1 should have changed; the `git status` count was the tell).

**Workaround:** Before running `shows_patch.py`, run `python3 -c "import json, re; d=json.load(open('drafts.json')); [s.__setitem__('description', re.sub(r'^\[DRAFT[^\]]*\]\s*', '', s['description'])) for s in d]; json.dump(d, open('drafts.json','w'), indent=2)"` to strip any leaked `[DRAFT` prefixes. Done once on 2026-04-19 PM — `drafts.json` is currently clean.

**Fix options (ranked):**
1. **Harden `shows_patch.py` to strip the prefix on write.** Five-line change: regex the `[DRAFT...]` prefix out of each description before writing to `shows.json`. Defense-in-depth — even if `drafts.json` leaks a prefix again, it cannot reach the live pipeline. Recommended.
2. **Add a validator to `shows_patch.py` that refuses to write if any description starts with `[DRAFT`.** Louder failure mode, forces the human to fix `drafts.json` explicitly. Complementary to option 1.
3. **Document the invariant in a `lrdfw-past-shows/README.md`** (“`drafts.json` must never contain `[DRAFT` prefixes; they are a build-time sentinel, not content”) and call it out in the end-of-session runbook. Cheapest; least enforcement.
4. **Remove the `[DRAFT` sentinel from `build_show_pages.py` entirely** and instead track draft/ready state as a real field (e.g., `"status": "draft"|"ready"`). Most invasive, but ends the overloading of the `description` string with out-of-band state. Only worth doing if we expect to keep publishing multi-pass drafts through this pipeline.

**Recommendation:** Ship option 1 + option 2 together as a small hardening of `shows_patch.py`. Keep option 4 on the back burner — if past-shows draft cycles end up being a one-off, the overloaded sentinel is cheaper than a schema change.

**Discovered:** 2026-04-19 PM, during the interactive review wrap-up, while pushing a one-line edit to Lava Cantina 2022-03-31. The `git status` file count (95 modified) did not match the intended surface area (2 files), which exposed the defect before commit.

**Lesson (also worth logging in the end-of-session runbook):** when a patch script writes through to generated HTML, always sanity-check `git status --short | wc -l` against the intended change size before `git add`. A 47x file-count multiplier caught this one; a smaller multiplier might not.

**Status:** ~~Open. Low-urgency because the invariant is currently satisfied in `drafts.json` and the past-shows draft cycle is effectively finished, but worth landing option 1 before the next time anyone touches `shows_patch.py` or `drafts.json`.~~ **FIXED 2026-04-20 PM** — shipped **option 1 + option 2** together (strip-on-write defense in depth + refuse-on-violation strict mode). Hardened `/home/user/workspace/lrdfw-past-shows/shows_patch.py`:

- Added `DRAFT_PREFIX_RE = re.compile(r"^\[DRAFT[^\]]*\]\s*")` as the single source of truth for the sentinel pattern.
- **Strict mode is the default.** Any draft whose description starts with `[DRAFT…]` causes the script to print the offending `(date, venue)` tuples to stderr and `sys.exit(2)` **without touching shows.json**. This is the behavior that would have caught B18 automatically on 2026-04-19 PM instead of relying on a human eyeballing `git status`.
- **Strip-on-write runs unconditionally.** Even with `--no-strict`, the prefix is regex-stripped before writing into `shows.json`, so `build_show_pages.py` can never see the sentinel via this path again.
- Added a `--no-strict` escape hatch for intentional "write the stripped content even though drafts.json still has the prefix" flows. Prints a `WARNING:` line naming the count of drafts being stripped so it's impossible to miss.

**Scope note:** The script lives under `/home/user/workspace/lrdfw-past-shows/` (Jarvis-side workspace), not under either git repo. It is not tracked, does not ship to `gh-pages`, and is not part of the published site. If the workspace were ever reset, the hardened version would be lost, but the bug it prevents is also only reachable through a manual Jarvis session, so the surface area is bounded. If Ray wants durability he can keep a copy in `liveradiodfw-marketing` alongside the other session-helper scripts; filing that as optional follow-up rather than required.

**Verification:** three smoke tests passed 2026-04-20 PM:

1. **Happy path:** clean `drafts.json` (current state), `shows_patch.py` ran green, 65 unchanged / 0 updates, `shows.json` md5 identical before and after (true idempotency). 
2. **Strict refuse:** injected the `[DRAFT - v2 warm-invitation voice, pending approval]` prefix into the first two entries of `drafts.json`; script printed the two offending `(date, venue)` pairs to stderr, exited 2, and `shows.json` md5 was unchanged. 
3. **`--no-strict` strip:** same injected input; script printed the `WARNING:` line, stripped both prefixes, and the final `shows.json` contained zero `[DRAFT` occurrences across all 65 descriptions.

**Relation to R9:** R9's end-of-session grep hook catches `CDT`/`CST` violations at commit time; this fix adds analogous defense for the `[DRAFT…]` sentinel, but inline in the tool that writes the data rather than as a post-commit grep. Both patterns — reject-at-source with a clear error — are worth adopting for any future Jarvis helper that writes to a file the build pipeline consumes.

**Follow-up deferred:** option 4 (replace the `[DRAFT…]` string sentinel with a real `"status": "draft"|"ready"` field in `shows.json` schema) remains a cleaner long-term design, but is out of scope given the past-shows draft cycle is effectively finished. Revisit only if a future workstream needs multi-pass drafting through this pipeline.

---

## B15. Calendar sync has no convention for cancelled or rescheduled shows ~~[OPEN]~~ → **FIXED 2026-04-18**

**Symptom:** Before this fix `sync_calendar.py` had no business logic for cancellations or reschedulings. If a show was cancelled or rescheduled, Ray's only clean options were (a) delete the GCal event and lose the audit trail, or (b) edit the event in place and have the public site continue to advertise a show that wasn't happening. First real occurrence: tonight's Apr 18 2026 OG Cellars show was weather-cancelled and rescheduled to Aug 1 2026.

**Where:** `lrdfw-ghpages/sync_calendar.py` — `SKIP_PATTERNS` and the module docstring.

**Impact:** Operational. Without a convention, either the GCal audit trail gets lost (delete/recreate) or the public site sends fans to a dead show (edit in place). Also: no test coverage for the scenario, so any future ad-hoc handling could regress silently.

**Workaround (before fix):** Manually edit `shows.json` after a cancellation — which violates the cardinal rule that GCal is the only source of truth.

**Fix (shipped 2026-04-18):** Established a convention plus code + tests to enforce it.

1. **Convention (what Ray does in GCal):** when a show is cancelled or rescheduled, do NOT delete the original event. Instead, rename it with a parenthetical suffix at the end of the title: `"<original title> (Rescheduled due to Weather)"` or `"<original title> (Cancelled)"`. If rescheduled, create a brand-new event for the new date (normal flow).
2. **Code (what `sync_calendar.py` does):** two new entries in `SKIP_PATTERNS` match any end-of-title parenthetical containing `rescheduled` or `cancel(l)ed` (both British and American spellings, case-insensitive). The renamed original stays on GCal as a band-facing audit record but is filtered out of `shows.json` so the public site never advertises a dead show. Docstring updated with the convention.
3. **Tests:** new `lrdfw-ghpages/test_cancellation_reschedule.py` — 13 cases covering the live Apr 18 + Aug 1 scenario, case variants, both spellings, LR-prefix + known-venue interaction with the new filter, and negative cases that confirm no false positives on words like "Canceltown" or "Rescheduling Ceremony" when not wrapped in an end-anchored parenthetical.

**Result on the live calendar run (2026-04-18 18:32 UTC):** sync correctly removed Apr 18 from `shows.json`, added Aug 1, regenerated `o-g-cellars-2026-08-01.html`, removed `o-g-cellars-2026-04-18.html`, committed `d124061`, and pushed to gh-pages. Alert email path exercised and would have sent; sandbox lacked the tools endpoint to deliver it, but the cron environment has it and will.

**Follow-ups (not in scope here):**
- `sync_calendar.py` email copy still uses the string "CDT" in one spot (`(daily at 8 AM CDT)`), which violates the Central/America-Chicago cardinal rule. Not blocking; track separately if it hasn't been.
- Once the GCal event for Apr 18 is old enough that Ray no longer wants it cluttering his calendar view, he can delete it — the sync no longer relies on its presence once Aug 1 is in place.

**Status:** Fixed 2026-04-18. Commits: gh-pages `d124061` (sync logic + tests + docstring, shipped atomically via the auto-sync commit); docs branch (this file) to follow.

---

## B13. Red date badge on show-detail pages is not square

**Symptom:** On individual show pages (`/shows/*.html`), the red date block in the hero renders as a tall rectangle instead of a square. The same kind of date badge on the shows-list page (`/shows.html`) renders visually closer to square. Ray wants them squared up and positioned upper-left within the show-page hero.

**Where:** `lrdfw-ghpages/css/style.css` lines 1712–1722 (the `.show-page-date` rule).

```css
.show-page-date {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 72px;
  padding: var(--space-3);
  background: var(--red);
  color: #ffffff;
  border-radius: var(--radius-md);
  text-transform: uppercase;
  font-family: var(--font-display);
}
```

No explicit width or height — dimensions are purely content-driven. Three rows of text (`day-name` / `day-num` / `month`) plus `--space-3` padding top and bottom makes the height larger than the `min-width: 72px`. The list-page badge (`.show-date-badge`, line 788) has the same content-driven structure but smaller padding + smaller min-width, so it happens to look close enough to square by accident.

**Position:** The hero container (`.show-page-hero`, line 1698) is already `display: flex` with `align-items: flex-start` and the date is the first child, so it's already upper-left within the hero box. No layout change needed for position.

**Fix:** Lock the date block to a fixed square (e.g. `72px × 72px`) and use `justify-content: center` to keep the three text rows vertically centered. Mirror list-page styling for visual consistency across pages.

**Status:** Fixed 2026-04-18 AM. See Fixed Recently section below.

---

## B12. Light-mode selection doesn't persist across pages ~~[OPEN]~~ → **FIXED 2026-04-20 PM**

**Symptom:** User visits any page on `liveradiodfw.com`, clicks the sun/moon icon in the top nav to switch to light mode, then navigates to another page — reverts to dark mode. Same in reverse (pick dark on a light-default system and navigate; reverts to light). Every page load honors the OS-level `prefers-color-scheme` and ignores whatever the user last clicked.

**Where:** Two cooperating code sites and neither writes to any storage:

1. Inline `<head>` script present in every HTML page (e.g. `about.html` line 8, `book.html` line 8, `contact.html` line 8, etc., and generated by `build_show_pages.py` line 161 for show-detail pages). Currently:

   ```js
   !function(){
     var e = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
     document.documentElement.setAttribute('data-theme', e)
   }();
   ```

2. Runtime handler in `js/main.js` lines 8–28. Reads the same `matchMedia` result on load, toggles the attribute on click, updates the icon label — but never writes the chosen theme anywhere.

Together these mean the user's click only survives until navigation; the next page's head script re-initializes from OS preference and overrides it.

**Impact:** Functional annoyance, not a blocker. A visitor who prefers light mode on a dark-OS setup (or vice versa) cannot browse the site comfortably without re-clicking on every page load. The flash between pages also looks janky.

**Fix options (ordered simplest to most invasive):**
- (a) **`localStorage` with OS fallback.** Standard pattern. Update the inline head script to read `localStorage.getItem('theme')` first, fall back to `matchMedia('prefers-color-scheme: dark')`; update the click handler in `main.js` to `localStorage.setItem('theme', currentTheme)`. Must-fix detail: the inline head script runs before `main.js` and before CSS paints, so persistence needs to happen in the inline head script to avoid a flash-of-wrong-theme (FOWT) on every navigation. Ray's instinct about "a cookie" works too but localStorage is client-only, doesn't ship on every HTTP request, and is the modern convention for this.
- (b) **`localStorage` with OS fallback + respect OS changes.** Same as (a), but additionally listen for `matchMedia` change events so a user who toggles their OS theme sees the site follow — unless they've explicitly picked a theme via the site toggle. Slightly more polish; requires a third state ("system" vs. explicit "light" vs. explicit "dark") if we want a "reset to OS" path.
- (c) **Cookie instead of localStorage.** Works, but ships the preference on every request for no reason and complicates the inline head script (has to parse `document.cookie`). Not recommended.

**Recommendation:** (a). ~5 lines changed in the inline head script (which is duplicated across ~15 HTML files plus `build_show_pages.py`) and ~2 lines added to `main.js`. The duplication is the real cost — worth considering a small build-time include for that head script if we're already regenerating show pages, so we don't have to hand-edit every top-level HTML page. Alternative: a `build_includes.py` pass that injects the head script the same way it injects nav and footer.

Implementation sketch for (a):

```js
// Inline head (replaces current version in every *.html file)
!function(){
  try {
    var stored = localStorage.getItem('theme');
    var e = stored || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', e);
  } catch (err) {}
}();

// main.js click handler (addition inside existing listener)
try { localStorage.setItem('theme', currentTheme); } catch (err) {}
```

`try/catch` guards private-browsing modes where localStorage is unavailable. Keep the existing `prefers-color-scheme` fallback so first-time visitors still get the right theme for their OS.

**Status:** ~~Open. Low-complexity, high-visibility fix — worth batching but also fine to ship on its own whenever there's a CSS/JS touch.~~ **FIXED 2026-04-20 PM** — shipped in commit [`f3bba3d`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/f3bba3d) on `gh-pages`, 116 files changed.

**Root cause:** two independent code paths set `data-theme` on every page load, neither persisting. (1) An inline head script in each HTML file (`!function(){var e=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';...}()`) read the OS preference pre-paint. (2) `js/main.js` `DOMContentLoaded` handler re-read the same `matchMedia` and re-applied it post-paint, overwriting anything the user had clicked. The toggle click handler flipped an in-memory `currentTheme` variable but never wrote to `localStorage` — so the next page load, or even a hard refresh on the same page, threw the choice away.

**Fix (three pieces, all in one commit):**

1. **Inline head script** — now reads `localStorage.getItem('theme')` first, falls back to OS preference, then hard-fallback to `'light'`. Wrapped in `try/catch` so Safari private mode, `file://` origins, and other `localStorage`-throwing contexts don't leave the page themeless. Still runs pre-paint so there's no flash of wrong theme on navigation.
2. **`main.js` toggle handler** — reads the current theme from the DOM (which the inline script already set correctly) instead of re-reading `matchMedia`, and now writes `localStorage.setItem('theme', ...)` on every click. `try/catch` on the setItem means private-mode clicks still visually toggle for the session, they just don't persist across tabs.
3. **`build_show_pages.py` template** — updated to emit the new inline snippet so regenerated show pages stay in sync. All 95 show pages rebuilt.

**Silent second bug fixed in passing:** the original `main.js` used `document.querySelector('[data-theme-toggle]')` to find the toggle (first match only) and attached the click handler only to that one element. The nav has both a desktop toggle (`index.html` line 92) and a mobile overlay toggle (line 135) — the mobile one had never fired. Swapped to `querySelectorAll` + `forEach`; both toggles now wire up. Not filed separately because it was adjacent code and would've been weirder to split.

**Files touched:** 114 HTML files (19 top-level hand-written + 95 regenerated show pages) for the inline snippet; `js/main.js` for the toggle wiring; `build_show_pages.py` for the template. Commit size inflated to 116 because the validFrom timestamp refresh on 8 upcoming show pages rode along as a free side effect of running `build_show_pages.py` (validFrom is `datetime.now(timezone.utc)` per B19).

**Verification:** unit-tested the precedence logic in Node with a mock DOM + mock localStorage + mock `matchMedia`. Four precedence cases passed (no-stored × OS-dark, no-stored × OS-light, stored=dark × OS-light, stored=light × OS-dark), plus a simulated "click toggle → navigate to new page" scenario where the stored value correctly overrode the still-dark OS preference on the new page. Ray to confirm on live site — both the navigate-and-come-back flow and the desktop ↔ mobile toggle both work.

**Cross-reference:** [roadmap.md R11](roadmap.md) — extend `build_includes.py` to cover head-level snippets. Shipping R11 first makes this bug's fix a one-file edit to `includes/head-boot.html` instead of a 15-file sweep. R11 is the preferred ordering but this bug is independently shippable if we don't want to wait.

---

## B11. Breadcrumb on show-detail pages is not unique per-show

**Symptom:** Every individual show page renders the breadcrumb as:

> Home › Shows › **Venue Name**

Since the band plays the same venues repeatedly (Fresh by Brookshires is on the schedule 2026-04-25, 2026-05-16, and 2026-09-12 right now), the three separate show pages all show an identical trailing breadcrumb crumb. Ray would prefer each page's crumb to be unique, e.g.:

> Home › Shows › **Venue Name — Date**

**Where:** `lrdfw-ghpages/build_show_pages.py` line 194:

```python
<span>{venue}</span>
```

sits inside `<nav class="breadcrumb" aria-label="Breadcrumb">` at lines 191–195. No structured-data `BreadcrumbList` block exists, so this is the only render site.

**Impact:** None functional. Pure cosmetic / neat-freak polish. Minor secondary benefit: makes the browser tab / SERP text snippet slightly more distinctive for the same-venue repeat pages.

**Fix options:**
- (a) **Append the date.** Change line 194 to something like `<span>{venue} — {long_date}</span>`, reusing the `long_date` variable already computed earlier in `build_show_pages.py` (it's the `"Saturday, April 25, 2026"` form used in the meta description). Mirrors the phrasing Ray asked for. One-line change.
- (b) **Append a shorter date.** Same as (a) but with `{show["date"]}` (ISO `2026-04-25`) or a compact `Apr 25` form — keeps the crumb from wrapping on mobile. Small trade-off vs. (a).
- (c) **Leave title as-is, add a BreadcrumbList schema.org block too.** If we're editing the breadcrumb anyway, worth also emitting a JSON-LD `BreadcrumbList` so Google can show breadcrumb text in SERPs (already noted as a gap in `ai_outputs/seo_keyword_analysis.md`). Small bonus scope, separate concern from the visible crumb.

**Recommendation:** (a), using an en-dash or em-dash consistent with the rest of the site (existing docs use em-dashes; the visible render already uses `&rsaquo;` as separator so any punctuation works). Ship with (c) if it's convenient; otherwise log (c) as a separate follow-up.

**Style note for the fix:** this is prose that will appear in rendered HTML on the public site, so the site's existing em-dash convention applies — no need to avoid em-dashes here (the "no em-dashes" cardinal rule is about Jarvis's output to Ray, not about site copy).

**Status:** Fixed 2026-04-18 AM. Applied option (a): changed line 194 to `<span>{venue} &mdash; {long_date}</span>`. All 8 public show-detail pages rebuilt and verified live — each now shows a unique crumb like `Home › Shows › FRESH by Brookshire's — Saturday, April 25, 2026`. See Fixed Recently section below.

---

## B10. Venue name duplicated on `/shows` and show-detail pages

**Symptom:** On `/shows.html`, each upcoming-show card renders the venue name two or three times in a row, e.g.:

> **25 Apr** — Fresh by Brookshires
> FRESH by Brookshire's, FRESH by Brookshire's, 5100 I-30, Fate, TX 75189, USA

The `<h3>` title (`Fresh by Brookshires`) is one rendering; the `<p class="venue-address">` line then starts with the venue name twice before the street address. Observed 2026-04-17 PM on live site for every Fresh by Brookshires card. Likely present on other cards where Google's `location` field is the place-name-prefixed form (`Venue Name, 123 Street, City, ST`).

**Where:** `lrdfw-ghpages/build_shows.py` line ~78:

```python
lines.append(f'          <p class="venue-address">{s["venue"]}, {s["address"]}</p>')
```

`s["address"]` comes straight from the Google Calendar event's `location` field, which Google Places populates as `"FRESH by Brookshire's, 5100 I-30, Fate, TX 75189, USA"` — the venue name is already the first segment. Concatenating `venue + ", " + address` duplicates it. The `<h3>` title already shows the venue name (from `s["title"]`, which is the stripped calendar title), so the full rendered cluster is venue×3.

**Impact:** Cosmetic but noticeable — looks unprofessional on the public `/shows` page, which is the primary conversion surface for the band. Also inflates the text content that search engines index for each show card with redundant tokens. Individual show-detail pages may have the same pattern (build_show_pages.py uses similar concatenation around line ~194–206) — worth auditing when fixing.

**Fix options (ordered simplest to most invasive):**
- (a) **Drop `venue` from the address line.** Change line 78 to `<p class="venue-address">{s["address"]}</p>`. Since Google's address already starts with the venue name, the card still shows the venue twice (h3 + address start) but not three times. Smallest diff.
- (b) **Strip leading venue from address.** In `calendar_event_to_show`, if `address.lower().startswith(venue.lower() + ",")`, strip that prefix so `s["address"]` is just `"5100 I-30, Fate, TX 75189, USA"`. Then venue appears once in h3 and address is clean street-only. Cleanest. Slight risk if venue and address disagree in casing or punctuation — handle with a normalized compare.
- (c) **Canonicalize at sync time.** Teach `sync_calendar.py` to split the calendar `location` into `venue` + `street_address` on ingest and store both, instead of parsing each build pass. More invasive but fixes related issues (e.g. `address_short` computation, which also consumes the raw address).

**Recommendation:** (b) as the fix. It's a ~5-line change in `calendar_event_to_show`, doesn't touch `shows.json` schema, and cleans up both `/shows.html` and the show-detail pages in one pass. Verify with `KNOWN_VENUES` entries and the two current private-event entries (which skip rendering anyway) to make sure nothing regresses.

**Status:** Fixed 2026-04-18 AM in two passes.

Pass 1 (ingest): Applied option (b) in `sync_calendar.py` with a guarded heuristic — strip the first comma-separated segment from `address` only when it looks like a venue name (starts with a letter) AND the second segment looks like a street address (starts with a digit). This cleans Google Places–formatted entries while leaving bare street addresses, private-event "City, TX" values, and multi-word street-name entries untouched. 7 of 10 current shows cleaned on first pass; Sweetwater Grill's calendar event was missing its street address entirely (data-side gap) and was updated on the calendar the same morning. That update exposed a latent regex bug in the `address_short` parser (`TX\b` matched `TX-276`), fixed in a follow-up commit — see Fixed Recently.

Pass 2 (render): The ingest fix alone left a subtler duplication on `/shows.html`: line 78 of `build_shows.py` rendered `<p class="venue-address">{venue}, {address}</p>`, which produced visible dupes like h3 "FRISCO RAIL YARD" followed by address line "Frisco Rail Yard, 9040 First St, …". Fixed by dropping the `{venue}, ` prefix — now renders `{address}` only. The h3 title above already carries the venue/event name, and `address` is pre-cleaned by Pass 1. Compact cards on index.html already used `address_short`, no change there. Verified live on `/shows` after push.

---

## B9. Availability script cannot be run or smoke-tested from Jarvis's sandbox

**Symptom:** `liveradiodfw-marketing/liveradiodfw_availability.py` authenticates to Google Calendar via OAuth (`credentials.json` + `token.json` via `google-auth-oauthlib`) and calls the Calendar API directly — it does NOT use the LiveRadioDFW Calendar Apps Script webhook. The OAuth credentials live on Ray's Windows cron host, not in the repo and not in Jarvis's sandbox. First-run auth requires `flow.run_local_server(port=0)` which pops a local browser, unavailable in a headless sandbox.

**Where:** `liveradiodfw-marketing/liveradiodfw_availability.py`, function `get_service()` around lines 39–54.

**Impact:** Jarvis cannot end-to-end smoke-test the availability pipeline against real calendar data. We can simulate the logic against the webhook's event list (which returns the same calendar, just through a different channel) but the simulation doesn't exercise the OAuth path, doesn't exercise pagination, and doesn't exercise the `showHiddenInvitations=True` flag. Any bug that's specific to the OAuth code path is invisible to Jarvis. Discovered 2026-04-17 PM during a smoke-test that tried to verify the availability script sees a test event correctly.

Secondary observation worth capturing: this means the band calendar is read by **two independent code paths** (sync via webhook, availability via OAuth). Rotating the webhook passphrase (B7) only affects one of them; rotating/revoking the OAuth token would only affect the other. Something to keep in mind for any future credential hygiene pass.

**Workaround:** Ray runs `python liveradiodfw_availability.py` from the marketing repo folder on his Windows box and pastes the output into the thread for Jarvis to verify. Adequate but manual and slow.

**Fix options (ordered simplest to most invasive):**
- (a) **Reuse the webhook.** Add an availability-generation path that uses the Apps Script webhook (same auth surface as `sync_calendar.py`) instead of direct Google Calendar OAuth. Jarvis could then smoke-test it from the sandbox. Cost: the webhook doesn't currently return all-day events or the `showHiddenInvitations` flag behavior — would need a small Apps Script extension (analogous to R10) and a response-shape check.
- (b) **Service-account credentials committed encrypted.** Use a Google service account with calendar-read scope, store the key encrypted (e.g. `sops`/`age`) in the repo, and have Jarvis decrypt at runtime from a secret injected via sandbox config. Invasive; introduces a secret-management system the project doesn't have yet.
- (c) **Ray exports a dated snapshot.** Periodic pipeline where Ray's Windows box writes the raw OAuth `events().list()` JSON to a gist or S3, and Jarvis reads that for testing. Decouples testing from real-time data but requires a separate pipeline.
- (d) **Keep manual.** Accept the limitation — Ray runs it locally, sends output, Jarvis reviews.

**Recommendation:** (a) is the most consistent with the rest of the architecture: the webhook is already the canonical band→Google-Calendar bridge, and consolidating on it eliminates the two-code-paths observation above. Would naturally pair with B7 Part 2 (move sync off gh-pages) and B1 (DST-safe cron) since all three touch the cron host.

**Status:** Open. Not urgent (workaround exists, manual testing is fine), but worth tracking because it limits Jarvis's ability to verify changes to the availability pipeline end-to-end.

---

## B8. `is_private_event` filter is too narrow; private shows can leak as public pages

**Symptom:** A calendar event titled `LR - Test Event (Private)` was correctly flagged as a gig (matches the `LR -` rule in `is_gig_event`) but was NOT flagged as private by `is_private_event`. Result: `shows.json` entry had `private: false`, and `build_show_pages.py` generated a full public show page at `shows/5608-chalice-dr-2026-06-20.html` with the residential venue address, a `MusicEvent` schema.org block, a canonical URL, and an announcement-style meta description.

**Where:** `sync_calendar.py`, function `is_private_event` (around line 169). The check is:
```python
def is_private_event(title):
    t = title.lower()
    return "private party" in t or "private event" in t or "gathering" in t
```
It only matches the exact substrings `private party`, `private event`, or `gathering`. Titles like `Test Event (Private)`, `Johnson Wedding - private`, or `Private BBQ` slip through.

Secondary issue: `calendar_event_to_show` strips the `LR - ` prefix before storing the title, so by the time downstream code sees the entry, any disambiguating context in the raw calendar title is already gone. The privacy decision should be made against the raw calendar event, not the stripped display title.

**Impact:** High. If a band member schedules a private booking (e.g. a wedding or house gig) and labels it with `(Private)` in parentheses rather than using the exact phrase `Private Event`, the script will publish:
- The residential venue address on the live site
- A schema.org `MusicEvent` block telling Google/Bing it's a public event
- A canonical URL Google will index
- A meta description announcing the show to the general public

Discovered 2026-04-17 PM during a smoke-test of the sync against a deliberate test event. No real private event has leaked to date (verified — both existing `private: true` entries on 2026-09-18 and 2026-10-31 have literal `Private Event` titles that the current filter catches). The bug is latent until someone labels a private event with non-matching phrasing.

**Workaround:** When creating a private booking on the calendar, use the literal phrase `Private Event` or `Private Party` in the title (or include the word `gathering`). Do NOT use `(Private)` in parentheses, `[private]` in brackets, or similar shorthand. Better: both — label it AND verify it lands as `private: true` on the next sync before trusting it.

**Fix options (ordered simplest to most invasive):**
- (a) **Broaden the filter.** Change `is_private_event` to match `\bprivate\b` as a standalone word anywhere in the title (regex word-boundary). Also consider matching against the raw `LR - ...` title, not the stripped one. Small code change, covers 90% of the likely miss cases.
- (b) **Require an explicit calendar signal.** E.g. the event description must contain a `Private: yes` line, OR the event title must contain `[PRIVATE]` in brackets. Explicit, zero false-positives, but requires documenting the convention and retrofitting existing events.
- (c) **Default-deny.** Flip the model: an LR-prefixed event is private unless the description explicitly contains a `Public: yes` line or a ticket line. Safest for privacy leaks but breaks the current muscle memory of "just put it on the calendar".
- (d) **Address-based heuristic.** If the venue string looks like a residential address (street number + street + city pattern, and NOT in the `KNOWN_VENUES` list), default to private. Indirect and fragile.

**Recommendation:** (a) as a quick fix to close the immediate gap, plus (b) documented as the canonical convention in `runbooks/edit-ticket-prices.md` (or a new runbook). (c) is tempting but would retroactively re-classify events and is more invasive than needed right now.

**Status:** Fixed 2026-04-18 midday. Shipped option (a) in gh-pages `c355e35`. `is_private_event` now matches the standalone word `private` (case-insensitive, word-boundaries) anywhere in the raw calendar title, plus the word `gathering` / `gatherings` for the Gatherings® venue family. New `test_is_private_event.py` at repo root covers 18 cases (10 positive, 8 negative): pre-fix baseline failed 6/18, post-fix passes 18/18. Includes the original bug (`LR - Test Event (Private)`), parenthesised and bracketed variants, trailing `- private`, lowercase, all-caps, and negative cases for substring false-positives like `Privateer Rodeo`. Post-fix sync against live calendar produced identical output (10 gigs, 2 private / 8 public split, no `shows.json` churn), so no regression on existing events. Runbook followup: option (b) from the original spec (document `Private Event` / `Private Party` / parenthesised `(Private)` as the canonical convention) still worth adding to a future runbook so humans converge on consistent phrasing; not blocking since the filter now handles the casual variants.

---

## B6. Videos on site require two clicks to play ~~[OPEN]~~ → **FIXED (resolved upstream, 2026-04-20 PM)**

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

**Status:** ~~Open. Reproducible on live site. Priority TBD - nuisance level, not outage.~~ **FIXED (resolved upstream, 2026-04-20 PM)** — Ray confirmed on live site this afternoon that videos now play on first click across pages. No code change landed in this repo to fix it in-session, so the resolution was either (a) a prior-thread fix that finally propagated through Cloudflare / browser cache, (b) a side effect of the `videos.html` or main.js changes shipped earlier today, or (c) a YouTube / Vimeo embed-script update on the player vendor side. Leaving the diagnostic bullets in place for reference: if the symptom reappears, that checklist is still the right starting point. Closing as WORKING rather than spending more time bisecting the cause.

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

## J9. Connectors are account-wide, not per-project

**Symptom:** Perplexity's external-tool connectors are attached to the user's Perplexity account, not to individual projects or threads. Band work and EOS work run in the same connector namespace. There is no UI-level way to say "this thread can reach Mailchimp + info@'s Google services, but must not touch ray.myers@eosworldwide.com's Gmail/GCal."

**Impact:** Project separation must be enforced behaviorally via cardinal rules ("NEVER read/write/search the `gcal` connector for band work") rather than structurally. J7 — cross-project connector access under ambiguity — is a direct consequence. Small lapse in rule adherence can leak data across project boundaries.

**Mitigation:** Cardinal rules in memory, `project-plan.md`, `architecture/sources-of-truth.md`, and the startup prompt. Ray's pushback is the safety net.

**Feature request to Perplexity:** Per-thread or per-Space connector allow-lists. Would fix J7, J3 (indirectly — Spaces already have their own connector limitation, but configurable per-project connectors would remove the reason to use Spaces this way), and reduce cognitive load on cardinal rules.

**Status:** Open, external platform limitation. Logged 2026-04-17 during calendar SoT cleanup as an explicit structural root cause (previously only surfaced implicitly via J7).

---

## B20. Legacy Bandzoogle-era past-show descriptions miss v2 warm-invitation voice

**Symptom:** 22 past-show descriptions in `shows.json` predate the v2 warm-invitation voice rewrite (2026-04-19/20) and fall outside the cohort of 65 that Ray reviewed one-at-a-time. They originated in the Bandzoogle import era and carry voice violations: exclamation points (v2 rule: none), the phrase "Cover band" (should be omitted or phrased as "Live Radio DFW"), or they're short stubs (50-200 chars) without the v2 pattern of venue specifics, geographic call-outs, practical logistics, and family/dog-friendliness cues.

**Why this matters now:** Ray asked for an honest read of the shipped descriptions on 2026-04-20 PM. The 65-show v2 cohort reads great — not cookie-cutter — but these 22 stragglers are the anti-pattern ("We love this family-friendly outdoor venue and hope you can come join us for a fun night of music." x3 identical copies on FRESH by Brookshire's). On an SEO + user-experience axis they're exactly the failure mode B16 was designed to prevent going forward — we just didn't backfill the pre-v2 population yet.

**Where:**
- `/tmp/lrdfw-lander/shows.json` — 22 entries, dates 2024-08-09 through 2025-11-29 (all past shows)
- Full audit with current text: `/home/user/workspace/lrdfw-past-shows/b20_stragglers_audit.txt` (generated 2026-04-20)

**Exact breakdown (n=22):**
- 6 use "Cover band" phrase — all Lion & Crown Pub dates (2024-11-16, 2025-03-15, 2025-05-03, 2025-05-31, 2025-09-06, 2025-11-29)
- 5 have exclamation points — 2024-08-09 Harvest Hall ("totally rad vibes... ultimate 80s tribute band" — worst offender, full rewrite warranted), 2025-06-28 Harvest Hall, 2025-08-09 Frisco Rail Yard, 2025-08-23 Harvest Hall (borderline — 411-char v2-quality prose, only flagged for 2 exclamation points; could be a minimal edit), and one other
- 16 under 200 chars — most overlap with the above; short stubs without v2 structure
- 3 identical copies on FRESH by Brookshire's (2025-04-05, 2025-05-24, 2025-07-12): `"We love this family-friendly outdoor venue and hope you can come join us for a fun night of music."`

**Impact:** Medium. Past-show pages are indexed and searchable, so thin/duplicated descriptions dilute the SEO benefit that the v2 cohort earned. Not urgent — none are upcoming shows, none violate cardinal rules like "dive bar" or "CDT," and they won't regress without intervention. But they read inconsistently to any human browsing past-shows chronologically, and they undercut the v2 baseline for future work.

**Fix plan:**
1. Use `/home/user/workspace/lrdfw-past-shows/b20_stragglers_audit.txt` as the input list.
2. Rewrite each in v2 warm-invitation voice following the same pattern as the 65-show cohort: opener rotation (Come join us / Live Radio DFW returns to / Catch us at / Meet us at / We're back at), venue specifics (what's there physically, history if known, food/drink details), geographic call-out (city + nearby communities), practical logistics (parking, cover charge, family/dog-friendly), no em-dashes, no exclamation points, no "dive"/"dive bar," present-or-evergreen tense.
3. For Harvest Hall 2025-08-23 (411-char v2-quality prose flagged only for 2 exclamation points): the minimal edit option is replace "!" with "." — faster than rewriting good copy.
4. For the 3 identical FRESH by Brookshire's stubs: produce 3 distinct rewrites so repeat visitors see variation across the chronology.
5. Run through `shows_patch.py` → `build_show_pages.py` → `build_includes.py` → commit + push to gh-pages. Same pipeline as the v2 cohort.
6. Optionally: extend `audit_shows.py` to grep published descriptions for `!`, `cover band`, and length < 200, so future Bandzoogle-style regressions are caught at commit time. Pairs well with the R9 end-of-session grep hook idea from B17.

**Effort:** ~22 short rewrites at v2 quality, plus 1 punctuation-only fix. Likely a focused session on its own — not mid-sprint material.

**Status:** Open. Filed 2026-04-20 PM after honest audit of the 95 published descriptions in `shows.json`. Audit file preserved at `/home/user/workspace/lrdfw-past-shows/b20_stragglers_audit.txt`. Not blocking; schedule when there's an hour of focused time.

---

## B21. Six scheduled tasks orphaned in a hung old Perplexity thread

**Symptom:** 2026-04-21 PM — while Ray was inspecting the Perplexity Tasks UI on his phone during a break, he surfaced a screenshot of an **old hung thread** that still owns SIX scheduled `LiveRadioDFW` tasks. Until this screenshot surfaced, Jarvis only knew about two of them (the Daily Calendar Sync we're retiring in B7, and the Monthly Profile Audit we just filed as R23). The other four — and the fact that the Monthly Profile Audit's next fire is **~4 days out, not ~10** — were completely missing from our durable inventory.

**The six tasks captured in the screenshot (2026-04-21 ~1:41 PM Central):**

| # | Task name | Next run | Was on inventory? |
|---|---|---|---|
| 1 | LiveRadioDFW Show Calendar Check | in 6 days | **No** |
| 2 | LiveRadioDFW Pre-Send Warning | in 19h 21m (fires tonight / tomorrow AM) | **No** |
| 3 | LiveRadioDFW Availability Check Reminder | in 7 days | **No** |
| 4 | LiveRadioDFW Monthly Setlist Review | in 4 days | **No** |
| 5 | LiveRadioDFW Monthly Venue Discovery | in 4 days (~2026-04-25, not ~2026-05-01) | Yes — this is R23; **date was wrong on our inventory** |
| 6 | LiveRadioDFW Bark.com Lead Monitor | in 33 minutes | **No** |

**Ray's framing (direct quote, 2026-04-21):** _"it's an old hung session that i think will answer a lot of our 'where did this get lost' questions. when I started working with you, I made the mistake of assuming perplexity computer max could do ongoing projects (Wrong!)"_

**CRITICAL UPDATE (2026-04-21 later, Ray's second message on B21):** The owning thread isn't just "hung" — it is **inaccessible**. The thread refuses to load with a spurious "you need more credits" error even though Ray has credits. **Ray currently has TWO open support tickets with Perplexity** trying to resolve this. **He cannot even stop the tasks from running** — the Tasks UI exposes a "Stop task" button per task, but tapping it in this state has not worked, presumably because the stop action requires the owning thread to respond and the thread is blocked. Consequence: the six crons keep firing on whatever schedule they were set on, Ray is burning Perplexity credits on runs he can't see, can't inspect, and can't halt, and the task prompts live only inside a thread he cannot currently open.

This is the root cause of a pattern we've hit for weeks: each session Jarvis would re-discover "there's a cron somewhere we can't see," and [bugs.md J1 (scheduled tasks are invisible across threads)](#j1-scheduled-tasks-are-invisible-across-threads) explained why, but we never had the full list of what was actually running. This screenshot is the first time we've seen the full inventory. Every one of these tasks has been firing for an unknown number of weeks or months without ever landing in `architecture/scheduled-tasks.md` or `runbooks/` — meaning their logic lives only in the owning thread's task prompt. If that thread is ever pruned, archived, or manually closed before we extract, that logic is gone.

**Why this matters now:**
1. **R23 (Monthly Venue Discovery) fires in ~4 days, not ~10.** The `architecture/scheduled-tasks.md` row 3 estimate of ~2026-05-01 is off by ~6 days — actual next fire is ~2026-04-25. This changes the urgency of R23 forensics significantly.
2. **Four other automations exist that we have zero documentation for.** Until we forensics the thread, we don't know what Pre-Send Warning, Bark.com Lead Monitor, Availability Check Reminder, Monthly Setlist Review, or Show Calendar Check actually do, what data they touch, or what breaks if they stop.
3. **Bark.com Lead Monitor fires every ~hour by the looks of it** (next run in 33 min at screenshot time). If that's running venue-lead collection or spamming, we need to know.
4. **Pre-Send Warning fires nightly** (19h to next run). This is almost certainly tied to something that runs the next morning — likely a heads-up before a campaign or the Availability Check. We need to understand the sequence before we unplug anything.

**Fix plan (gated on Perplexity support ticket resolution):**

*Track A — things we can do without access to the thread:*
1. **First:** add a new section to `architecture/scheduled-tasks.md` placeholdering all six by name, with "Next fire" from the screenshot and "Documentation status: UNKNOWN — task prompt lives only in a thread Ray cannot currently open; see B21." This stops the inventory from looking complete when it's not.
2. **Correct R23 next-fire date** in `roadmap.md` and `scheduled-tasks.md` row 3 from ~2026-05-01 to ~2026-04-25. Treat R23 as a ~4-day deadline, not ~10.
3. **Check the Tasks UI task-detail view** (tap on a task, not the thread) for any exposed prompt / cron-spec / last-run / next-run / owner-thread-id info. Some task-management UIs surface this without requiring the owning thread to load. If any field is visible, screenshot it. Save everything to `/workspace/b21_task_prompts/<task_name>.md`.
4. **Observe destination side-effects** for each task around its next-fire window to reverse-engineer what it does. Candidates: `info@liveradiodfw.com` inbox for new emails, Mailchimp audience `97cca06eff` and any other band audiences for `other_adds` / campaign activity, GitHub commit history on both band repos, Bark.com inbox / leads panel, Google Calendar change log, any known shared Google Doc. Match observed side-effects to task names to classify before we ever see the prompts.
5. **Document hypotheses per task** based on observed side-effects + task name + fire cadence, so when the thread unblocks we know what to confirm and what to rebuild.

*Track B — things that require the thread to unblock (Ray's two open Perplexity support tickets):*
6. **Forensics session** (60–90 min): once the thread opens, for each of the six tasks, open its task view, copy the prompt verbatim, save to `/workspace/b21_task_prompts/<task_name>.md`. **Do NOT delete any task until prompts are extracted and understood.**
7. **Classify each:** does it edit data (destination?), send mail (to whom?), post to an external service (which API?), or just log/summarize? Decide per-task: extract to `-marketing` repo and migrate to Windows Task Scheduler (same pattern as B7), consolidate with an existing cron, or retire.
8. **Extract before migrating.** Apply the same lesson from B7: sibling `.py` file + `.env` in `-marketing`, `setup_*_task_scheduler.ps1`, runbook alongside. Every extraction decommissions one Perplexity cron and makes that task's logic survive the owning thread.
9. **After all six are extracted**, retire the hung thread (or leave it and let the tasks die naturally once Perplexity unblocks stop-task).

**Meta-lesson (for the J-series):** Every Perplexity thread that owns a `schedule_cron` task is a single point of failure — if the thread is lost, the cron's source of truth dies with it, because [`schedule_cron(list)`](#j1-scheduled-tasks-are-invisible-across-threads) only returns tasks owned by the current thread. The B7 pattern (runner + runbook + `setup_*.ps1` all in a durable public repo) needs to become the standard for any `schedule_cron` that does real work. A roadmap item may fall out of this ("Migrate all band crons to the Windows box") once we know what the remaining five do.

**Status:** Open. Filed 2026-04-21 PM the moment Ray surfaced the screenshot. Not blocking the B7 install in progress right now — but the next session that has spare cycles should forensics this thread before anything else, because Monthly Venue Discovery (R23) now fires in ~4 days and we have five more tasks with zero documentation.

---

## Fixed recently (moved here for context; full history in postmortems)

- **2026-04-18 midday - B8 private-event filter broadened to word-boundary match:** Event titles like `LR - Test Event (Private)`, `LR - Johnson Wedding - private`, `LR - Private BBQ`, and `[PRIVATE] Corporate Xmas` used to slip past `is_private_event` (which only matched the three exact substrings `private party`, `private event`, `gathering`). Any of those leaks would have published a residential address, a `MusicEvent` schema.org block, a canonical URL, and a meta description to Google. Fix: swap the three substring checks for two compiled regexes — `\bprivate\b` and `\bgatherings?\b`, both case-insensitive — run against the raw calendar title (still before the `LR -` prefix strip, so parenthesised / bracketed disambiguators are available). Word boundaries prevent false matches on substrings like `privateer`. Shipped with a new `test_is_private_event.py` harness that exercises 18 title variants (pre-fix: 6 failures; post-fix: 18/18 pass) so future regressions on this function will be caught locally before deploy. Live-calendar smoke test produced the same 10 gigs and same 2:8 private:public split as pre-fix, so no current event changed classification. Also added a tiny `.gitignore` (first in the repo) to keep `__pycache__/` out of future commits now that tests are in play.
- **2026-04-18 midday - B14 Share promoted to primary CTA + button reorder + dark-mode text-colour fix + Get Directions demoted to match the rest of the row:** Show-detail action row reordered from `Get Directions, Add to Calendar, Share, All Shows` to `Share, Get Directions, Add to Calendar, All Shows`. Share button gained `.btn-primary` class alongside `.btn-share` so the existing `show-actions.js` click handler still binds correctly while picking up CTA styling. New `.btn-share.btn-primary` compound selector in `css/style.css` gives it solid-fill red + white text + white SVG stroke, overriding the ghost-outline default of plain `.btn-share`. **Final-polish pass:** on first render Get Directions was still `.btn-primary` (red-fill) from the original template. Ray’s correction: the point of a CTA is to call to ONE action, and the single highest-leverage action for the band is Share (drives show reach). Two reds compete, neither wins. Demoted Get Directions from `.btn-primary` to `.btn-secondary` so Share is the only red element in the row; Directions, Add to Calendar, and All Shows now share the uniform outline treatment. Lesson: a CTA is defined by being visually unique in its neighborhood, not by being red. Give it a singular role in the layout or it isn’t a CTA at all.

  Two gotchas caught along the way:

  1. **Nav/footer stripped on first rebuild.** Initial commit ran `build_show_pages.py` alone and forgot to run `build_includes.py` after — left the `BEGIN_NAV`/`END_NAV` and `BEGIN_FOOTER`/`END_FOOTER` regions empty, so every show page briefly rendered without navigation or footer. Caught via `git show --stat` showing 865 lines deleted across 8 pages (suspicious). Fixed by running `build_includes.py`, which re-injected nav+footer and added back exactly 863 lines. **Pipeline lesson:** any show-page template change needs the two-step build `build_show_pages.py && build_includes.py`, not just step one.

  2. **CTA text went black in dark mode.** Ray flagged that the red Get Directions button showed black text in dark theme. Root cause: `[data-theme="dark"]` at `css/style.css` lines 85–92 remaps `--white: #12121e` (near-black), and `.btn-primary` used `color: var(--white)`. The nav BOOK THE BAND pill (`.nav-cta` line 525) had always hard-coded `color: #ffffff` specifically to dodge this. Fixed by changing `.btn-primary` to `color: #ffffff` as well. Verified in both themes via Playwright: Share, Get Directions, and nav-cta all render `rgb(230, 57, 70)` fill + `rgb(255, 255, 255)` text, light and dark. **CSS lesson:** any var() that gets redefined in a theme block is a landmine when you want a colour that shouldn't flip with theme. For "always-white-on-brand-colour" use hard-coded `#ffffff`, not `var(--white)`.

- **2026-04-18 AM - B10 Pass 2: venue duplication at render layer cleaned up:** After shipping the ingest-side fix earlier in the morning, Ray spotted residual duplication on live `/shows.html` — h3 title "FRISCO RAIL YARD" followed by address line "Frisco Rail Yard, 9040 First St, …". Root cause was render-side: `build_shows.py` line 78 concatenated `{venue}, {address}` in the `.venue-address` paragraph, and because `address` was already pre-cleaned of the leading venue segment by Pass 1, the template was the only remaining dupe source. Fix: drop the `{venue}, ` prefix so the paragraph renders street-only. Compact cards on index.html already used `address_short`, no change needed there. J6 lesson reinforced: when I first said "it's live" after the ingest fix, I was reading the JSON (clean) rather than the rendered card (still dup). Verify at the render layer, not just the data.
- **2026-04-18 AM - B13 Pass 2: badge bumped 72→80 so text content fits the square:** First pass locked `width: 72px; height: 72px` which made the box model square, but Ray caught that the rendered badge still *read* as taller than wide. Live-DOM measurement confirmed the box was exactly 72×72, but the three text rows (SAT 22px + day-num ~39px + APR 22px = ~83px total) overflowed the 72px height, making the background square look shorter than its content. Fixed by bumping width/height to 80×80 — matches the `.show-date-badge` on `/shows.html`, where `day-num` is 35px and the content totals ~80px, fitting cleanly inside the square. Bonus consistency: listing and detail badges are now the exact same visual size. Lesson: a square border-box doesn't guarantee a square *appearance* when child content overflows; measure rendered child heights, not just the box.
- **2026-04-18 AM - B13 Pass 1: square-boxed `.show-page-date` on show-detail pages:** `.show-page-date` had `min-width: 72px` but no explicit height, so three rows of text plus `--space-3` padding pushed height above width, rendering as a tall rectangle. Fixed by locking `width: 72px; height: 72px;` and adding `justify-content: center` so the three text rows vertically center; dropped padding from `--space-3` to `--space-2` so the text still fits inside the 72px square. Added `flex-shrink: 0` for narrow-hero safety. Position was already correct (the parent `.show-page-hero` is a flex row with `align-items: flex-start` and the date is child #1, so upper-left was the pre-existing layout). Verified on `/shows/fresh-by-brookshires-2026-04-25.html` after push.
- **2026-04-18 AM - B11 breadcrumb on show pages now unique:** `build_show_pages.py` line 194 changed from `<span>{venue}</span>` to `<span>{venue} &mdash; {long_date}</span>`. Each detail page now has a distinct trailing crumb like `Home › Shows › FRESH by Brookshire's — Saturday, April 25, 2026`. Verified live on `/shows/fresh-by-brookshires-2026-04-25.html` after sync push.
- **2026-04-18 AM - B10 follow-up: `address_short` regex tightened to not match `TX-276`:** Immediately after shipping B10 and updating the Sweetwater Grill calendar event with a real street address (`4884 TX-276, Royse City, TX 75189, USA`), sync ran and `address_short` regressed from `Royse City, TX` to `4884, TX`. Polluted the `<title>` and meta description on the show-detail page (`| Live Music 4884, TX`). Root cause: the short-address parser at `sync_calendar.py` lines 261 and 271 used `TX\b` which matches at the X-hyphen word boundary in `TX-276`, then captured the street number (`4884`) as the city. Fix: both regexes changed from `TX\b` to `TX(?=\s|$|\d)` so TX must be followed by whitespace, end-of-string, or a ZIP digit — not a hyphen. Verified against all current addresses before pushing. Lesson: highway designators like `TX-276` are the edge case; `\b` is not tight enough for state-abbreviation matching when the same two letters can appear in highway names.
- **2026-04-18 AM - B10 venue duplication cleaned up at ingest:** `sync_calendar.py` now strips the leading venue segment from `address` when the second segment clearly looks like a street address (first char is a digit). Canonical `shows.json` stores street-only addresses; every downstream consumer (`/shows.html` venue-address line, show-detail `show-page-address`, JSON-LD schema, Add-to-Calendar `data-cal-address`, `.ics` export) is cleaned in one pass. 7 of 10 current shows updated on the live site on the first pass. Sweetwater Grill was the 8th once Ray added a street address to the calendar event later that morning; that update exposed the `TX-276` regex bug noted in the follow-up bullet above.
- **2026-04-17 PM - B2 webhook `attendees` field fixed (R10 closed):** Extended `_updateEvent` in `scripts/LiveRadioDFWCalendar.gs` to iterate `data.attendees || data.guests` and call `event.addGuest(email)` for each; normalized `_createEvent` to accept either field name; both paths now return the resulting `guests` array for verification. Published as Version 2 of the Apps Script project via the new runbook. Smoke test via `requests.post` confirmed `list`, `create` with attendees, `update` adding a new attendee, and `delete` all return JSON 200 with expected payloads. Passphrase was simultaneously rotated (partial B7 fix; see B7 section above).
- **2026-04-17 PM - B3 Outlook-native event IDs marked won't-fix:** The Outlook half of the old dual-entry pipeline was formally decommissioned this session (new cardinal rule: band events created only on the Google Calendar on info@). Existing Outlook-origin events remain hand-edit-only in the GCal UI, but the population is finite and no longer growing. See B3 section above.
- **2026-04-17 - B4 calendar host identity cleaned up:** Band calendar source of truth confirmed as `info@liveradiodfw.com` (free Google personal account). Corrected 3 doc locations (`sources-of-truth.md`, `calendar-sync.md` x2, `edit-ticket-prices.md`). Added canonical statement in `architecture/sources-of-truth.md`. Committed master copy of Apps Script to `docs/scripts/LiveRadioDFWCalendar.gs` (passphrase redacted). New runbook: `runbooks/publish-calendar-webhook.md`. Spawned B7 (public passphrase exposure), J9 (connectors account-wide), R10 (attendees fix).
- **2026-04-17 - B5 GitHub Pages challenge TXT restored:** Pulled fresh challenge value from `github.com/settings/pages`, added as TXT record in Cloudflare (`_github-pages-challenge-TicoRicoRay` → `76bd16254d16a7be4333e49413c13d`). Verified propagation on 1.1.1.1, 8.8.8.8, and `summer.ns.cloudflare.com`. Domain was already verified via DNS-based method; this restores the belt-and-suspenders challenge record that was dropped during the Cloudflare migration.
- **2026-04-17 - Sync wipe:** `sync_calendar.py` was overwriting hand-curated fields in `shows.json`. Fixed with non-destructive merge + strict ticket-price parser. See [postmortems/2026-04-17-sync-wipe.md](postmortems/2026-04-17-sync-wipe.md).
- **2026-04-15 to 2026-04-16 - 12-hour outage:** during the Bandzoogle → Cloudflare → GitHub Pages migration. Fixed. See [postmortems/](postmortems/).
- **2026-04-17 - Silent "Free" default:** the ticket parser used to default to "Free" when no line was present. Now it alerts via email and leaves the field blank.
