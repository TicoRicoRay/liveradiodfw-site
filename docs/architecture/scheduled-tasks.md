# Scheduled Tasks - Live Radio DFW

_Last updated: 2026-04-21 PM (B7 Part 2 **installed live on Ray's Windows box**; Windows Task Scheduler entry registered green and Ready; 3-day parallel-run window runs 2026-04-22 through 2026-04-24)_

Every scheduled/recurring job that touches the band, where it runs, what it does, and how to find or modify it. Nothing automated should exist off this list - if a future agent creates a new scheduled task, add it here the same day.

## Why this file exists

Perplexity `schedule_cron` tasks are **thread-scoped**. A task created in thread A is invisible from thread B, even to the same account. Running `schedule_cron(list)` in a new thread returns an empty array even when tasks are actively firing elsewhere. That's how we spent half of 2026-04-17 AM hunting for a daily sync that nobody in the active thread could see. This file is the only durable inventory.

---

## 1. Daily calendar sync

**Status 2026-04-21 PM:** Windows Task Scheduler entry **registered and Ready on Ray's box as of this afternoon** (B7 Part 2 install complete). Task name `LiveRadioDFW Daily Calendar Sync` at root path `\`, daily 8:00 AM Central trigger, verified via `Get-ScheduledTask`. Manual smoke-test run of `python sync_runner.py` returned clean "Everything in sync. No issues found" (stub-email path). **First scheduled production fire: 2026-04-22 08:00 Central.** Parallel-run verification window: **2026-04-22 through 2026-04-24**, both the Windows task and the Perplexity `schedule_cron` fire daily; once Windows logs 3 consecutive clean runs with identical commit shape, the Perplexity task gets deleted. The Perplexity row is kept below for history; the Windows row is the new primary.

**Known caveat (tracked by [roadmap.md R24](../roadmap.md#r24-windows-task-scheduler-run-whether-logged-on-mode-switch)):** the Windows task runs in "Run only when user is logged on" mode, not "run whether logged on or not." Ray uses Windows Hello for daily unlock and the local account password isn't saved anywhere, so the set-and-forget mode switch was deferred. If Ray is logged in (screen locked is fine), the task fires. If the PC is fully logged out or shut down at 8 AM, the day is skipped. Watch the 3-day parallel-run for skipped days; promote R24 if the miss rate bites.

### Primary host (new, 2026-04-21 onward)

| Field | Value |
|---|---|
| **What** | `sync_runner.py` runs end-to-end: loads `.env` → calls Apps Script webhook → parses ticket prices → imports pure logic from `sync_lib.py` (pulled fresh from `gh-pages` at run start) → non-destructively merges into `shows.json` → regenerates per-show HTML pages → git commit + push to `gh-pages` → emails `info@liveradiodfw.com` on missing data |
| **Where it runs** | **Windows Task Scheduler on Ray's PC.** Task name: `LiveRadioDFW Daily Calendar Sync`. Install dir: `C:\Tools\LiveRadioDFW\liveradiodfw-marketing\` (a `git clone` of the public [`liveradiodfw-marketing`](https://github.com/TicoRicoRay/liveradiodfw-marketing) repo — Ray `git pull`s updates forever, no zip downloads). |
| **Runbook** | [`liveradiodfw-marketing/docs/windows-sync-task.md`](https://github.com/TicoRicoRay/liveradiodfw-marketing/blob/master/docs/windows-sync-task.md) (canonical copy ships with the code it installs). |
| **When it fires** | **8:00 AM Central daily**, DST-safe by construction (Task Scheduler uses local time and handles DST automatically). Closes [bugs.md B1](../bugs.md#b1-calendar-sync-cron-drifts-across-dst) once the Perplexity cron is retired. |
| **Secrets** | `C:\Tools\LiveRadioDFW\liveradiodfw-marketing\.env` (gitignored, hand-created from `.env.example`, never committed). Source of truth for values: 1Password Secure Note "LiveRadioDFW Calendar webhook passphrase." |
| **Commits as** | `LiveRadioDFW <info@liveradiodfw.com>` via HTTPS + Git Credential Manager on the Windows box. |
| **Cost** | Zero Perplexity credits. Runs on local machine. |
| **Manual run** | `cd C:\Tools\LiveRadioDFW\liveradiodfw-marketing && python sync_runner.py` |
| **Task registration** | One-time: run `.\setup_sync_task_scheduler.ps1` as Administrator from the repo root (registers the Task Scheduler entry). Re-run if the schedule changes. **Install history:** first registration attempt 2026-04-21 PM failed (`-WakeToRun $false`, WakeToRun is a switch param, takes no value); fix pushed as `-marketing` commit `1a50a7c`; second attempt clean green. Filed as [bugs.md J10](../bugs.md#j10-jarvis-ships-untested-windows-scripts) (pattern: Jarvis ships untested Windows PowerShell when test environment is the user's box). |
| **Logon mode** | "Run only when user is logged on", see status block above + [roadmap.md R24](../roadmap.md#r24-windows-task-scheduler-run-whether-logged-on-mode-switch). Switch to "run whether logged on or not" deferred because it requires the local account password (Ray uses Windows Hello only). |
| **Closes** | [bugs.md B7](../bugs.md#b7-webhook-passphrase-and-url-are-publicly-readable-on-the-live-site) (exposure) and [bugs.md B1](../bugs.md#b1-calendar-sync-cron-drifts-across-dst) (DST drift) as a pair. |

---

## 2. Monthly venue-availability email

| Field | Value |
|---|---|
| **What** | `run_availability.bat` runs `liveradiodfw_availability.py` (queries band calendar, computes open Fridays/Saturdays for next 6 months, writes `availability.json`), then `send_availability_email.py` (clones a Mailchimp template campaign, injects dates between `<!-- AVAILABILITY_DATES_START --> / END --> ` markers, sends to the Venues audience) |
| **Where it runs** | Windows Task Scheduler on Ray's PC |
| **Path** | `C:\Users\myers\Downloads` (hardcoded in `setup_task_scheduler.ps1`) |
| **When it fires** | Every Tuesday at 9:00 AM Central |
| **Gate** | Scripts internally check "is this the last Tuesday of the month?" and exit otherwise |
| **Effective cadence** | Once per month |
| **Logs to** | `availability_log.txt` in the same Downloads folder |
| **Mailchimp config** | Venues audience `97cca06eff`, template campaign `6f64a2aba3` ("March 2026 Availability" draft), server prefix `us6`. API key is in `send_availability_email.py` line 24 on the local machine only, never in the repo |
| **Repo for scripts** | [`liveradiodfw-marketing`](https://github.com/TicoRicoRay/liveradiodfw-marketing), `master` branch |
| **Bugs filed** | None currently |

### How to verify it's running

On Windows: open Task Scheduler, find "LiveRadioDFW Availability Email" (or whatever name `setup_task_scheduler.ps1` registered). Check "Last Run Time" and "Last Run Result." `availability_log.txt` holds script output.

### How to force a send

Run `run_availability.bat` manually. Note that the last-Tuesday gate in the scripts will block sends on other days unless you comment it out temporarily.

---

## 3. Monthly Profile Audit (venue discovery)

| Field | Value |
|---|---|
| **What** | Searches the DFW metroplex for new live-music venues and adds any net-new finds to the Mailchimp **Venues audience** (`97cca06eff`) so they land on the monthly availability-email list. First band-marketing project Ray built with Jarvis. |
| **Where it runs** | Perplexity `schedule_cron` task named "LiveRadioDFW Monthly Profile Audit" |
| **Owned by** | Perplexity thread "More Band Marketing" (per Ray's Perplexity Tasks view 2026-04-21). `schedule_cron(list)` returns empty from any other thread — see [bugs.md J1](../bugs.md#j1-scheduled-tasks-are-invisible-across-threads). |
| **When it fires** | Monthly — next fire observed ~2026-05-01 from the Perplexity Tasks UI (10-day countdown on 2026-04-21). Exact cron expression not yet extracted; lives inside the owning thread. |
| **Evidence it's working** | Mailchimp Venues audience activity 2026-03-30 shows **15 `other_adds` in one day** — the monthly batch. Afterwards a trickle of 1-3 subs/day as Ray hand-processes incoming adds. Verified via Mailchimp API 2026-04-21. |
| **Script location** | **Not yet extracted.** Script logic currently lives only inside the owning Perplexity thread's task prompt. Loss risk is real — see R23. |
| **Cost** | Burns Perplexity credits per run. |
| **Roadmap entry** | [roadmap.md R23](../roadmap.md#r23-preserve-and-document-the-monthly-profile-audit-venue-discovery-cron) — extract, commit to `-marketing`, migrate to Ray's Windows Task Scheduler alongside the B7-Part-2 `sync_runner.py`, then delete the Perplexity task. |
| **Cardinal reminder** | The owning thread ("More Band Marketing") is the ONLY place the script currently exists. Do not archive or lose that thread until R23 ships. |

### How to find and edit the owning thread

1. Open Perplexity in-app → Tasks view (as of 2026-04-21 the icon sits above History/Spaces/Customize/Computer in the left nav).
2. Find "LiveRadioDFW Monthly Profile Audit."
3. Click through to the owning thread — it's labeled "More Band Marketing" unless Ray has renamed it.
4. The task prompt in that thread IS the full spec — copy it verbatim before editing.

### How to verify the last run fired

Query Mailchimp Venues audience activity for the last 45 days (API: `/3.0/lists/97cca06eff/activity`). A single-day spike of 5+ `other_adds` is the cron firing. Trickle adds on other days are Ray hand-processing.

---

## Deleted / defunct tasks (for context)

### Hourly SSL cert watcher (DELETED 2026-04-17)

Ran hourly between Apr 16 evening and Apr 17 morning during the HTTPS outage, polling GitHub Pages for cert provisioning status and emailing on change. Deleted after the Cloudflare migration stabilized the cert situation. Action item #13 on [postmortems/2026-04-17-sync-wipe.md](../postmortems/2026-04-17-sync-wipe.md) marks this **Done**.

### LiveRadioDFW Daily Calendar Sync, Perplexity cron (DEFUNCT 2026-04-24, still firing)

Ran daily at 13:11 UTC from Perplexity `schedule_cron` in the thread "More Band Marketing." Triggered the pre-split monolithic `sync_calendar.py` on `gh-pages` until 2026-04-21, when B7 Part 2 shipped and replaced the host with Windows Task Scheduler on Ray's box. Parallel-run window (2026-04-22, 23, 24) completed clean on 2026-04-24; retired in the same motion as [B1](../bugs.md#b1-calendar-sync-cron-drifts-across-dst--open--fixed-2026-04-24-structural-fix-via-b7-part-2-parallel-run-window-clean) / [B7](../bugs.md#b7-webhook-passphrase-and-url-are-publicly-readable-on-the-live-site--open--fixed-2026-04-21-part-2-shipped-exposure-closed).

**Why "defunct" and not "deleted":** Ray cannot reach the "More Band Marketing" thread to delete the `schedule_cron` task. As of 2026-04-24, new Perplexity Computer threads silently drop Computer and connector access on submit (reproduced across 2 browsers + Windows client; support's only response was to stop submitting tickets), so the Tasks UI for the old thread is not accessible either. The cron is therefore still firing daily at 13:11 UTC.

**Why it is harmless:** `sync_calendar.py` was removed from `gh-pages` on 2026-04-21 and renamed to `sync_lib.py`, which is a pure library with no `__main__` block and no side effects. If the old Perplexity thread's cron ever tries to invoke the old path, it hits a 404 / import error and produces nothing.

**How to fully delete:** Once new Computer threads work again, or Perplexity auto-expires the old thread, open "More Band Marketing" -> Tasks -> delete `LiveRadioDFW Daily Calendar Sync`, then update this row to DELETED with the date.

---

## Rules for adding new scheduled tasks

If you (future Jarvis) create a new scheduled task for this project:

1. **Document it here before you leave the thread.** Do not rely on "I'll remember" or "someone will see it in Perplexity's UI." Thread-scoped means invisible the moment the session ends.
2. **Note the owning thread identifier if possible.** Even a short name/date helps the next Jarvis locate it for modification.
3. **Prefer schedules that are DST-safe from the start.** Use Python to convert Central to UTC for the exact month of creation, but also note the drift behavior in this table so someone catches it before winter.
4. **Log the credit cost** if the task runs in Perplexity - it affects Ray's monthly usage.
5. **Cross-link to any bug** that the task is meant to address or any runbook that explains manual equivalents.
