# Live Radio DFW — Project Plan

_Last updated: 2026-04-23 AM Central (session closed with Ray's directive: "assume this buggy mousetrap we've built is NOT working -- test before proceeding" next session. R25 Part A, R26 cache-purge tool, and 3 Nations description all shipped, but the 3 Nations ship surfaced a silent build-chain skip (see B33 / R27) that is the reason for the directive. B7 3-day parallel run continues. Prior update: 2026-04-21 PM -- B7 install LIVE on Windows box.)_

**This file is the session-to-session handoff.** For active defects see [bugs.md](bugs.md). For planned work see [roadmap.md](roadmap.md).


## 🚀 Starting a new session

Perplexity threads are disposable. This repo is the durable memory. To get a new agent up to speed fast, paste this as your first message:

> **Band marketing work on Live Radio DFW. Start the 60-min timer. Then: [today's task].**
>
> _Memory should carry: name (Jarvis), cardinal rules (EOS separation, Central not CDT/CST, no em-dashes in public-facing content only (site, Mailchimp, venue/fan emails) — internal docs are fine, no "15 minutes" estimates, GCal source of truth for shows, Mailchimp for venue contacts, Cloudflare for DNS, `gh-pages` serves the site), and the docs-read trigger (on the phrase "Live Radio DFW" / "the band" / "band marketing", read https://github.com/TicoRicoRay/liveradiodfw-site/tree/docs - `docs/project-plan.md` first including "Pick up here next session", then `docs/bugs.md`, `docs/roadmap.md`, `docs/architecture/scheduled-tasks.md`, `docs/architecture/connectors.md` (which connectors are band-active vs. off-limits - critical because connectors are account-wide, not project-scoped), skim `docs/architecture/sources-of-truth.md` and `docs/runbooks/`, then the public site at https://www.liveradiodfw.com, and also review https://github.com/TicoRicoRay/liveradiodfw-marketing - the sibling marketing repo that hosts the monthly venue-availability Mailchimp automation, marketing style guide, and setlist theme analysis; `-site` and `-marketing` work together). Follow the "How to add" templates at the top of `bugs.md` / `roadmap.md` for any new bug or roadmap entry - no exceptions. "Wrap up" / "close out the thread" / "end of session" triggers the checklist at `docs/runbooks/end-of-session.md`._
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

## READ FIRST NEXT SESSION - Ray's directive (2026-04-23 end of session, verbatim)

> "Next session - top priority - assume this buggy mousetrap we've built is NOT working. Test before proceeding."

**What "the mousetrap" is:** Everything that ran this session, and especially the pieces that shipped with confidence but had hidden gaps.

**Before touching any of it, verify it actually works end-to-end.** Pre-flight tests to run in this order:

1. **3 Nations live description.** `curl -s https://www.liveradiodfw.com/shows/3-nations-brewing-2026-09-05.html | grep -c "rolls into 3 Nations Brewing"` must return `1`, AND `grep -c "show-page-description-placeholder"` must return `0`. If either fails, the commit `ee5a8e2` didn't land or GH Pages didn't rebuild.
2. **Builder chain idempotency.** Clone `liveradiodfw-site/master` fresh, run `build_shows.py` -> `build_show_pages.py` -> `build_includes.py` with no JSON edits. `git status` should be clean (or only timestamp-field deltas on unchanged shows). If real content diffs appear, a builder is non-deterministic; investigate before any new shows.json write.
3. **B7 Windows sync.** Check `gh-pages` commit log: did the 8:00 AM Central run on 2026-04-23 fire from the Windows box? Did it fire on 2026-04-24 by the time the session opens? If commits are missing, B7 is not actually live. (Parallel-run verification for B7 was scheduled 4/22-4/24; this is the last day of that window.)
4. **R25 Part A email shape.** Read back the most recent alert email for a new show; verify the APPROVE / EDIT mailto buttons render in Outlook iPhone and that the token in the subject matches `approvals/pending.json`. If the email is stubbed per B22 (just stdout on Windows), note it; Part B is blocked anyway.
5. **R26 purge_cache.py.** On the Windows box, `python purge_cache.py --shows --dry-run` should print 3 URLs without hitting the API. Then a real `--shows` run should print "Cache purged" AND `Verified: <URL> cf-cache-status=<status>` lines that are all MISS/DYNAMIC/EXPIRED/BYPASS. If any verify line is HIT, the purge silently failed (that's exit code 3, built in).
6. **Pre-commit hook for shows.json (R27).** Does not exist yet. Until it does, any write to `shows.json` MUST be followed by running the three builders and staging the resulting `shows/*.html` changes. If you catch yourself editing `shows.json` without the builders, STOP; you just reproduced the bug that triggered this directive.

**Why Ray said this:** The 3 Nations description was committed to `shows.json` as commit `5f768ed` without running the builder chain. The live site kept showing the placeholder. Ray had to catch it. The failure had zero error signal: commit succeeded, push succeeded, working tree clean, Cloudflare cache status irrelevant. This class of silent failure is what "buggy mousetrap" refers to: components that look wired up but aren't, or are wired up but skip steps. Every new thing we shipped this session (R25 Part A approval workflow, R26 cache-purge, R27 builder-chain guard) is a candidate for the same kind of hidden gap. **Test each before building on it.**

**Test-before-proceed applies recursively:** if a test fails, fix the test harness, don't work around it. If a test passes in dry-run but not on the Windows box, that is a finding, not a nuisance.

---

**Context (2026-04-23 AM session, approval-workflow track):** **R25 Part A shipped: reply-to-approve workflow for show descriptions.** Surfaced when Ray asked whether the 2026-09-05 3 Nations Brewing show had a description (it did not) and identified the automation gap: every new public show lands in `shows.json` with no description, the sync emails a proposed draft to `info@liveradiodfw.com`, but nothing can act on that draft without a full Jarvis session. Fix: APPROVE / EDIT mailto buttons in the alert email with a stable 12-char sha256 token in the subject line. Reply from Outlook on iPhone or desktop -> Part B (next session) IMAP poller on the Windows box consumes the token -> writes `shows.json[show].description` -> commits as "Ray" -> pushes to master. Part A landed sync_lib helpers (`approval_token`, `build_approval_email_section`), sync_runner wiring, six new test cases (all pass), `approvals/pending.json` scaffold with schema, and this architecture doc. B32 filed as the defect, R25 as the three-part plan. Next session picks up with Part B (`process_approvals.py` on Windows box + second Task Scheduler entry every 15 min + sender allowlist + cardinal-rule gate + expiry). Until Part B ships, approvals still round-trip through a session, but the email now tells Ray exactly what to reply and carries the token so we can process retroactively.

**Context (2026-04-23 AM session, 3 Nations Brewing description):** Concrete instance of the workflow gap. Draft for the 2026-09-05 Carrollton show produced by `generate_description_draft` ([DRAFT] prefix, 395 chars, ASCII-clean). Actual v2 warm-invitation description to be authored this session after Part A lands; applied to `shows.json` as a same-session manual commit since Part B is not yet live. This also becomes the first pending-approval record and the first data point for the Part C decision.

**Context (2026-04-21 PM session, SEO track):** **B25 shipped: `build_includes.py` now manages canonical + og:url + sitemap as a third single-point-of-maintenance block alongside nav and footer.** Every page (root + 95 `shows/*`) stamped with `<link rel="canonical" href="https://www.liveradiodfw.com/<slug>">` (extensionless, www-normalized to match live serving host). Sitemap regenerated from the same page list: 112 → 114 extensionless URLs. `home.html` deleted as a true orphan (Cloudflare `/home*` 301 remains as insurance). Only exclusion is `nav.html` (legacy fragment, kept for `build_nav.py`). PR #1 on `master` open for merge. **B26 filed** for the dual nav source-of-truth (`nav.html` + `includes/nav.html`) that B25 surfaced. Also **R4 partially mitigated**, and **roadmap/runbook docs scrubbed** of prescriptive `.html` URLs where they remained.

**Context (2026-04-21 PM session, install track):** **B7 Part 2 install is LIVE on Ray's Windows box.** First production sync from Windows pushed real changes to `gh-pages` ([`06bc1cb`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/06bc1cb), a `Gatherings®` mojibake cleanup on the 2026-09-18 Private Event). Windows Task Scheduler task `LiveRadioDFW Daily Calendar Sync` is registered, `Ready`, and fires daily at 8:00 AM Central, DST-safe by construction (B1 auto-closes on Perplexity cron retirement). Full install path: Ray cloned both repos to `C:\Tools\LiveRadioDFW\`, `pip install tzdata` for Python 3.14 zoneinfo support, hand-edited `.env` with webhook URL + passphrase + repo path, confirmed idempotent second run ("Everything in sync. No issues found"), registered task via fixed `setup_sync_task_scheduler.ps1`.

**Status of B7:** Functionally complete. Formal close-out waits on 3-day parallel-run verification against the old Perplexity cron (which Ray can't stop anyway per B21, see below, so "parallel" is automatic; we just compare `gh-pages` commit authors/timestamps for the next 3 days). Both systems produce the same idempotent commit shape, so double-firing is cost-only, not correctness-risky. **B7 and B1 both close when the 3-day check clears AND the Perplexity cron is retired (which is gated on B21 / Perplexity support ticket resolution).**

**Three new items opened this session as spin-offs from the install:**
- **B21**, SIX scheduled tasks orphaned in a hung Perplexity thread. Tasks are firing but Ray cannot access the thread (spurious "credits exhausted" error), cannot stop them, has 2 support tickets open. Includes the daily calendar sync, a nightly pre-send warning, a weekly availability check, a monthly setlist review, the **R23 Monthly Profile Audit** (next fire ~2026-04-25, inventory said ~May 1 which was wrong by 6 days), and a Bark.com lead monitor running hourly. Task prompts live only in that thread, forensics blocked until support resolves. Preserved phone screenshot at `/home/user/workspace/b21_task_prompts/2026-04-21_tasks-ui-screenshot.jpg` inside the agent sandbox (Ray has the original on his phone).
- **B22**, `sync_runner.py` alert email stubbed on Windows (the `external-tool` subprocess is Perplexity-sandbox-only; doesn't exist on a Windows box). Stopgap shipped ([`afcfe45`](https://github.com/TicoRicoRay/liveradiodfw-marketing/commit/afcfe45)) that prints intended email to stdout. **Reframed mid-session per Ray (2026-04-21 2:06 PM Central):** _"The purpose of the email is 2 things - a friendly 'heads up' but also a chance for a human to be alerted if the cron job does something bad."_ This is a **production-safety watchdog**, not a cosmetic nicety. Cron pushes directly to production `gh-pages`; without the email, a bad sync (accidental deletes, mojibake regression, private-event leak) sits live until Ray notices organically. Fix path: Gmail SMTP app password, richer body with git diff-stat + warnings list + 🚩 REVIEW subject prefix when >N shows change in one run. Effort ~45-60 min. **Gates full B7 close-out.**
- **J10**, Jarvis blind spot: ships untested Windows scripts. `setup_sync_task_scheduler.ps1` shipped with `-WakeToRun $false` (wrong param kind, switch, not boolean), compounded by an unconditional success banner that printed below a stack trace. Ray caught it. Fixed in [`1a50a7c`](https://github.com/TicoRicoRay/liveradiodfw-marketing/commit/1a50a7c) by dropping the bad arg + adding `$ErrorActionPreference = "Stop"` + post-registration `Get-ScheduledTask` verification. Mitigation pattern filed for future PS1/.bat work.

**R24 filed, deferred Windows Task Scheduler mode upgrade:** Install registered the task in "Run only when user is logged on" mode because Ray uses Windows Hello (PIN/biometrics) and does not have the local account password memorized or in 1Password. Switching to "run whether logged on or not" would require a `netplwiz` reset with a small DPAPI side-effect footprint; punted as not-worth-it for a currently-theoretical failure (Ray is active on this machine daily). Runbook documents the known limitation. If the 3-day parallel run shows skipped days, R24 gets promoted.

**R23 reality check from B21:** The Monthly Profile Audit's "next fire ~May 1" estimate was WRONG by 6 days per the phone screenshot, actual next fire is ~2026-04-25 (4 days out). Forensics is still gated on B21 / Perplexity support ticket resolution. If support doesn't resolve before 4/25, Ray considers manually running the Mailchimp audience check that morning to avoid a month-long gap.

**No-zip handoff, reaffirmed:** Ray's 2026-04-21 quote, _"Rather than download zip files (like a caveman) - can we isolate any sensitive information in a single file - download it. Then everything else is just a pull from github as needed?"_, is now the governing pattern for this project's infra. Only `.env` is hand-managed; everything else is `git clone` once, `git pull` forever. Deleted stale `/home/user/workspace/b7-windows-handoff.zip` during session as part of this pattern.

**Install path convention locked in:** All GitHub clones live under `C:\Tools\` on Windows. For this project specifically: `C:\Tools\LiveRadioDFW\liveradiodfw-marketing\` and `C:\Tools\LiveRadioDFW\liveradiodfw-site\`. Saved to memory as `projects.liveradiodfw.clone_paths`. NEVER assume `C:\LiveRadioDFW` or `C:\Users\myers\Downloads`.

**Editor preference locked in:** Ray uses **VS Code**, not notepad. Feed him `code <filename>` commands. Saved to memory as `tools.code_editor`.

**Follow-ups queued but not yet filed as bugs (candidates for next session intake):**
- Webhook URL should live in 1Password alongside the passphrase. Came up when Ray found only the passphrase in the "LiveRadioDFW Calendar webhook passphrase" secure note and couldn't locate the URL. `.env.example` and runbook say "Website field" for the URL which is misleading since 1Password doesn't have it. Sourced this session from prior-session context (was in old `gh-pages/sync_calendar.py:57`).
- `requirements.txt` in `-marketing` so Windows install can say `pip install -r requirements.txt` instead of hunting `tzdata` after a ModuleNotFoundError. Python 3.14 on Windows specifically needs `tzdata` for `zoneinfo` to resolve IANA timezones like `America/Chicago`.
- `send_availability_email.py:27` still has `MAILCHIMP_API_KEY = "YOUR_MAILCHIMP_API_KEY"` placeholder, same anti-pattern B7 just fixed, never swept. Low priority but worth filing as B- eventually.

**Prior-session context (preserved for continuity):**

_2026-04-21 AM:_ B7 Part 2 library/runner split shipped to both repos. `sync_calendar.py` split into `sync_lib.py` (pure functions on `gh-pages`) + `sync_runner.py` (orchestration + secrets, published to `-marketing/master` at [`ee94c10`](https://github.com/TicoRicoRay/liveradiodfw-marketing/commit/ee94c10)). `fetch_historic.py` deleted as a sixth caller with no future use. 5 callers updated to `from sync_lib import …`; all 49 tests green. Exposure verified closed: `https://www.liveradiodfw.com/sync_calendar.py` → 404, GitHub raw → 404, passphrase no longer grep-able anywhere public. R23 filed separately after walking the Perplexity Tasks UI revealed the second cron. **J1 re-confirmed:** `schedule_cron(list)` returns empty from any thread that does not own the task. The way to find band crons is Perplexity in-app → Tasks view (left nav) → identify owning thread.

_2026-04-19:_ pure infrastructure cleanup. Opened a Bark.com bid for Ree's 6/7/26 birthday party (file in local workspace, not yet sent by Ray). Three-item sweep: **R2 closed** (UptimeRobot on free plan, HEAD-only 5-min checks, alerts to info@, dashboard password-protected). **R3 closed** (sitemap of 112 URLs to GSC, `/lander` re-index requested, `/home` deduplicated via Cloudflare Page Rule `*liveradiodfw.com/home*` → 301 → `https://www.liveradiodfw.com/`). **R9 closed** as a standing rule (build-time `audit_shows.py` + end-of-session runbook step 4 grep). Step 4 surfaced CDT strings at `sync_calendar.py:677` and `:731` which became **B17**. SEO belt-and-suspenders preference saved to memory (wildcard patterns covering apex/www, trailing slashes, file extensions, query strings).

**GSC connector is live** (2026-04-19, 9:00 AM Central). Property: **`sc-domain:liveradiodfw.com`** (Domain property, URL-prefix variants return no data). Two tools exposed: `retrieve-site-performance-data` and `submit-url-for-indexing`. Sitemap management and URL Inspection API are NOT exposed by this Pipedream connector, fall back to GSC UI or a native connector if needed. R19/R20/R21 filed and R4 enriched from the first audit.

**Heads-up for the NEXT thread specifically:** B7 install is shipped; B22 watchdog email is the next clean bite (~45-60 min, bounded). B21 forensics is blocked on Perplexity support. Top-of-funnel foundation work (R11, R22, B6) is still untouched. R4 reassesses 2026-05-03 after Google re-crawls.

**Top priorities right now:**

**0. (NEW, takes precedence) Run the pre-flight test battery at the top of this file.** Ray's 2026-04-23 directive: assume the mousetrap is broken, test before proceeding. Steps 1-6 above. Do not touch priorities 1-13 until the test battery passes or the failures are documented as new B-entries. If step 6 (pre-commit hook) is still missing, file it as the first action item, not a later one.


1. **B7 3-day parallel-run verification.** Windows task fires daily 8:00 AM Central; Perplexity cron in the inaccessible thread fires independently on its own schedule (can't stop it, see B21). For 3 consecutive days (2026-04-22, 23, 24) check `gh-pages` commit log: any sync-author commits should be from the Windows box only, OR the two systems should land on the same shows.json state by end-of-day. If they diverge, investigate. Day 1 baseline: Windows pushed [`06bc1cb`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/06bc1cb) at ~2:00 PM Central on 2026-04-21 (manual smoke test, the 8:00 AM scheduled run is 2026-04-22). Verify no divergence then formally close B7 + B1 and move the old Perplexity row to "Deleted / defunct tasks" in `architecture/scheduled-tasks.md`.

2. **B22 - sync_runner watchdog email**, see [bugs.md#b22](bugs.md). **Gates B7 full close-out.** Per Ray's 2026-04-21 reframe, the alert email is a production-safety tripwire for catching bad cron behavior (accidental deletes, mojibake regression, private-event leak), not a cosmetic heads-up. Recommended path: Gmail SMTP app password, richer body with git diff-stat + warnings list + 🚩 REVIEW subject prefix when >3 shows change in one run. Effort ~45-60 min, bounded. Next session's first tidy bite.

3. **B21 - 6 orphaned scheduled tasks in hung Perplexity thread**, see [bugs.md#b21](bugs.md). Blocked on Perplexity support ticket resolution (2 tickets open). Track A (can do without thread access): document what we know about each task from screenshot + inventory, plan manual-run fallbacks. Track B (needs support): forensics the task prompts, extract to code. **R23 Monthly Profile Audit is the most time-sensitive**, next fire ~2026-04-25 (not May 1, inventory was wrong by 6 days). If support doesn't resolve before 4/25, consider manually running the Mailchimp audience check that morning.

4. **R23 - Preserve the Monthly Profile Audit venue-discovery cron**, see [roadmap.md#r23](roadmap.md). Merges with B21 above, forensics blocked on thread access. Windows box from priority #1 is the migration target once extracted.

5. **B1 - DST-safe sync cron**, see [bugs.md#b1](bugs.md). **Auto-closes when #1 completes**, Windows Task Scheduler uses local Central time with automatic DST handling. Bookkeeping only.

6. **R22 - Station / Theme / Show taxonomy + named-show build-out**, see [roadmap.md#r22](roadmap.md). High-priority per Ray (2026-04-19 `/lander` smell-test). Two linked problems: (a) public-facing word for genre buckets vs. named themed products, is "Station" what people search for in nav? (b) A Tribute To MTV, Graduation Night, Texas Music Night, and other ready-to-book shows live only in the marketing repo and memory, needs inventory + runbook + pages. `gh-pages/stations.json` is orphaned. Strongly recommend R11 ships first so nav changes are single-file.

7. **D1 - ChatGPT site audit**, see "Pending discussion" below. Ray has audit findings to walk through before they become bugs or roadmap items.

8. **R11 - head-level include extraction**, see [roadmap.md#r11](roadmap.md). High-leverage foundation item; makes future template-level fixes (like B12) single-file edits instead of 15-file sweeps. Prerequisite for R22's taxonomy-driven nav changes.

9. **R4 - Wildcard 301s**, see [roadmap.md#r4](roadmap.md). Reassess 2026-05-03 after Google re-crawls following this session's `/home` 301. Enriched with concrete URL patterns from GSC audit.

10. **B6 - Videos two-click bug**, see [bugs.md#b6](bugs.md). Investigation-heavy; not a quick fix.

11. **R18 - Locale SEO landing pages**, see [roadmap.md#r18](roadmap.md). "Band-type in {city}" intent capture.

12. **R21 - Verify /home 301 consolidation**, see [roadmap.md#r21](roadmap.md). Fact-finding only, earliest check 2026-05-03. Natural pair with R4 reassessment.

13. **R24 - Windows Task Scheduler "run whether logged on or not"**, see [roadmap.md#r24](roadmap.md). Low priority, deferred. Only promote if the 3-day parallel run (#1) surfaces a skipped day.

**Recently closed:**
- **B7 Part 2 install live on Ray's Windows box (2026-04-21 PM):** First production sync from Windows pushed [`06bc1cb`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/06bc1cb) to `gh-pages` (a real `Gatherings®` mojibake cleanup on the 2026-09-18 Private Event). Windows Task Scheduler task `LiveRadioDFW Daily Calendar Sync` registered via `setup_sync_task_scheduler.ps1`, daily 8:00 AM Central, DST-safe. Install commits: [`4590122`](https://github.com/TicoRicoRay/liveradiodfw-marketing/commit/4590122) (path convention `C:\Tools\LiveRadioDFW\`), [`b9b0070`](https://github.com/TicoRicoRay/liveradiodfw-marketing/commit/b9b0070) (.env.example path fix), [`afcfe45`](https://github.com/TicoRicoRay/liveradiodfw-marketing/commit/afcfe45) (B22 stub for alert email), [`1a50a7c`](https://github.com/TicoRicoRay/liveradiodfw-marketing/commit/1a50a7c) (PS1 `-WakeToRun` fix + Stop-on-error guard), [`74c7d9f`](https://github.com/TicoRicoRay/liveradiodfw-marketing/commit/74c7d9f) (runbook R24 caveat). Docs commits: [`9044b79`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/9044b79) (runbook stub), [`f9e2aa3`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/f9e2aa3) (path sweep), [`7a2e326`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/7a2e326) + [`af9403b`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/af9403b) (B21 filing), [`6f872cd`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/6f872cd) + [`29cff5c`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/29cff5c) (B22 filing + watchdog reframe), [`1f0f8bb`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/1f0f8bb) (J10 filing), [`2629ca2`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/2629ca2) (R24 filing). 3-day parallel run in flight; formal B7 close-out waits on verification + Perplexity cron retirement (gated on B21).
- **B7 Part 2 shipped — exposure closed end-to-end (2026-04-21):** `sync_calendar.py` removed from `gh-pages`. New shape: `sync_lib.py` (pure functions, on `-site/gh-pages`) + `sync_runner.py` (orchestration + secrets from `.env` at runtime, published to public `-marketing/master`). `fetch_historic.py` deleted as a sixth caller with no future use. 5 callers updated to `from sync_lib import …`; all 49 tests green. Verified: `https://www.liveradiodfw.com/sync_calendar.py` → 404, GitHub raw → 404, passphrase no longer grep-able anywhere public (30-second window from push to Cloudflare edge propagation). Commits [`b125405`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/b125405) on `-site/gh-pages`, [`aca5b21`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/aca5b21) on `-site/docs`, and [`ee94c10`](https://github.com/TicoRicoRay/liveradiodfw-marketing/commit/ee94c10) on `-marketing/master`. No-zip handoff per Ray's architectural preference — Ray `git clone`s `-marketing` once, `git pull`s forever, only `.env` is hand-managed. Install + 3-day parallel run + retire Perplexity cron is the only remaining work (tracked as priority #1 above).
- **R23 filed — preserve the Monthly Profile Audit venue-discovery cron (2026-04-21):** Walking through the Perplexity Tasks UI surfaced a second cron in the "More Band Marketing" thread (besides the known daily calendar sync): the Monthly Profile Audit that populates the Mailchimp Venues audience `97cca06eff`. Mailchimp API confirmed it works (15 `other_adds` on 2026-03-30 = monthly batch). Script lives ONLY in that thread's task prompt — never extracted. Filed as R23 with plan to forensics-dump, extract to `liveradiodfw-marketing/venue_discovery/`, then migrate to the Windows box alongside `sync_runner.py`. Also added row 3 to `architecture/scheduled-tasks.md` so the cron is on the durable inventory regardless of thread fate. First band-marketing project Ray built with Jarvis. Commit [`3fc9e33`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/3fc9e33) on `docs`.
- **Past-shows interactive description review, 65/65 approved (2026-04-19 PM):** Ray walked through all 65 past-show descriptions one at a time with simple `go`/`change` responses. Result: **64 approved as-is, 1 rewritten** (Lava Cantina 2022-03-31 — seasonal phrase "A late-March Thursday show" removed; the venue reads evergreen now). Shipped as commit [`4f65317`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/4f65317) on `gh-pages`. During the push a latent defect surfaced in the drafts pipeline and is filed as **B18** below — caught before it could regress the 64 approved descriptions back to "Show details coming soon" placeholder. Ray's v2 warm-invitation voice is now the live state of every past-show page. No further work on past-show copy is queued.
- **R14 partial ship - press-kit opening aligned to `/lander` positioning + venues/planners proof block (2026-04-19 AM):** Press-kit bio paragraph rewritten to lead with "Same musicians playing together since 2021, now under one name after merging Risky Business DFW and Jackson Crossing" (Ray's mid-session correction to the initial "formed from the merger" framing — continuity is the selling point, rename is the footnote). New "For venues and planners" proof block with seven facts-only bullets: together since 2021, 5-piece / 5 vocalists, 100+ songs / 6 decades, ready-to-book themed shows (MTV / Graduation Night / Texas Music Night), in-ear monitors, fully insured, DFW-based. "Start here" pin on Band Overview video. Commits [`42965d4`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/42965d4) and [`e850c1a`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/e850c1a) on `gh-pages`. **R14 remains open** for the remaining scope: recent-venues strip (depends on R5 / hand-curation), set-length grid (needs Ray), starts-at price figure (needs Ray), standalone "Why book us" page or `book.html` section, and the R13 style-guide alignment pass.
- **R22 filed - Station / Theme / Show taxonomy + named-show build-out (2026-04-19 AM):** High-priority roadmap item from Ray's `/lander` smell-test. Two linked problems: naming / IA (is "Station" what people search for?) and the inventory of named ready-to-book shows that exist only in Ray's memory and the `-marketing` repo. Architecture discovery filed inline: `gh-pages/stations.json` is orphaned (zero references across HTML / JS / Python). R22 plan covers inventory, taxonomy resolution, `stations.json` fate decision, runbook for adding a themed-show page, and staged page builds. Commit [`2d01979`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/2d01979) on `docs`.
- **`/lander` graphic refinement (2026-04-19 AM):** Per Ray's smell-test, merger hero moved to the bottom of the merger section and shrunk from 640px to 360px max-width. `/lander` is less about the merger than about new business; graphic placement now reflects that. Commit [`20f7e4f`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/20f7e4f) on `gh-pages`.
- **R19 - `/lander` conversion audit shipped (2026-04-19 AM):** Rewrote title, meta, H1, opening paragraph, and CTA on `/lander` to lead with commercial booking intent ("Live Radio DFW - Dallas-Fort Worth Tribute & Cover Band for Hire") instead of the old merger-announcement framing. Merger content preserved and moved below the fold to keep bookmark-search traffic. New "Custom Tribute Shows" section surfaces three ready-to-book themed products (A Tribute To MTV, Graduation Night, Texas Music Night) using audience-first language — first draft used internal-memo framing and Ray flagged the mismatch before ship. Final copy demonstrates positioning through the product menu rather than announcing it. Single primary CTA (Book Live Radio DFW), dropped the weak Homepage button. Commits [`eae3ad8`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/eae3ad8), [`043866c`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/043866c), [`08daaa9`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/08daaa9), [`20f7e4f`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/20f7e4f) on `gh-pages`. Post-ship smell-test refinement (2026-04-19 10:42 AM Central, commit `20f7e4f`): Ray asked to move the merger graphic to the bottom of the merger section and shrink it, since the page is less about the merger than about new business — shipped at max-width 360px at the bottom of that section. See R19 in [roadmap.md](roadmap.md) for the measurement plan (4-week CTR check on 5/17) and philosophy notes. R14 updated in parallel with the final shipped copy as the press-kit starting point. **Indexing-API limitation discovered:** Pipedream's `submit-url-for-indexing` is restricted to `JobPosting`/`BroadcastEvent` schemas; for band URLs it no-ops silently. Ray should hit "Request indexing" in the GSC UI when convenient, or let natural re-crawl run. Logged in `architecture/connectors.md`.
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

### 2026-04-23 AM
- R25 Part A shipped: reply-to-approve workflow for show descriptions. `sync_lib.approval_token()` and `sync_lib.build_approval_email_section()` added; `sync_runner.py` now delegates to the helper when a description-missing show has a usable draft. APPROVE and EDIT mailto links with token in subject, plain text, Outlook-iOS-and-desktop friendly. `approvals/pending.json` + `approvals/README.md` scaffolded. Six new test cases in `test_description_handling.py` (token stability, cross-show invariance, cross-draft invariance, APPROVE mailto presence, EDIT mailto presence, ASCII-only, no em-dash / smart quote). All existing sync_lib tests still green. New `architecture/approval-workflow.md` documents Parts A/B/C and cardinal-rule gates.
- B32 filed: "No low-friction path to approve proposed show descriptions."
- R25 filed: three-part plan (Part A shipped, Part B queued, Part C deferred).
- 3 Nations Brewing 2026-09-05 v2 warm-invitation description authored and shipped to `shows.json` as same-session manual commit (Part B not yet live).

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
