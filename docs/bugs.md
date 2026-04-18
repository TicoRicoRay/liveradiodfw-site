# Live Radio DFW - Bug List

_Last updated: 2026-04-17 (calendar SoT cleanup session)_

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

## B7. Webhook passphrase and URL are publicly readable on the live site

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

**Status:** Partially addressed. Passphrase rotated (Part 1 of fix option (a)); sync script not yet moved off `gh-pages` (Part 2). Remains top priority until Part 2 lands.

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

**Status:** Open. Logged 2026-04-18 AM.

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

## B12. Light-mode selection doesn't persist across pages

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

**Status:** Open. Low-complexity, high-visibility fix — worth batching but also fine to ship on its own whenever there's a CSS/JS touch.

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

**Status:** Open. Not urgent because no real private event currently has ambiguous phrasing, but latent — the next private booking someone labels casually could leak a home address. Should fix before the next private event lands on the calendar.

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

## Fixed recently (moved here for context; full history in postmortems)

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
