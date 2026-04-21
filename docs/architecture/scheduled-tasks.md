# Scheduled Tasks - Live Radio DFW

_Last updated: 2026-04-21 PM (B7 Part 2 shipped; runner now lives in the public `liveradiodfw-marketing` repo — `git clone` once, `git pull` forever, no zip handoff)_

Every scheduled/recurring job that touches the band, where it runs, what it does, and how to find or modify it. Nothing automated should exist off this list - if a future agent creates a new scheduled task, add it here the same day.

## Why this file exists

Perplexity `schedule_cron` tasks are **thread-scoped**. A task created in thread A is invisible from thread B, even to the same account. Running `schedule_cron(list)` in a new thread returns an empty array even when tasks are actively firing elsewhere. That's how we spent half of 2026-04-17 AM hunting for a daily sync that nobody in the active thread could see. This file is the only durable inventory.

---

## 1. Daily calendar sync

**Status 2026-04-21:** Migrating from Perplexity `schedule_cron` → Windows Task Scheduler as part of B7 Part 2. During a 3-day parallel-run verification window both tasks fire daily; once the Windows task is confirmed green, the Perplexity task gets deleted. The Perplexity row is kept below for history; the Windows row is the new primary.

### Primary host (new, 2026-04-21 onward)

| Field | Value |
|---|---|
| **What** | `sync_runner.py` runs end-to-end: loads `.env` → calls Apps Script webhook → parses ticket prices → imports pure logic from `sync_lib.py` (pulled fresh from `gh-pages` at run start) → non-destructively merges into `shows.json` → regenerates per-show HTML pages → git commit + push to `gh-pages` → emails `info@liveradiodfw.com` on missing data |
| **Where it runs** | **Windows Task Scheduler on Ray's PC.** Task name: `LiveRadioDFW Daily Calendar Sync`. Install dir: `C:\LiveRadioDFW\liveradiodfw-marketing\` (a `git clone` of the public [`liveradiodfw-marketing`](https://github.com/TicoRicoRay/liveradiodfw-marketing) repo — Ray `git pull`s updates forever, no zip downloads). |
| **Runbook** | [`liveradiodfw-marketing/docs/windows-sync-task.md`](https://github.com/TicoRicoRay/liveradiodfw-marketing/blob/master/docs/windows-sync-task.md) (canonical copy ships with the code it installs). |
| **When it fires** | **8:00 AM Central daily**, DST-safe by construction (Task Scheduler uses local time and handles DST automatically). Closes [bugs.md B1](../bugs.md#b1-calendar-sync-cron-drifts-across-dst) once the Perplexity cron is retired. |
| **Secrets** | `C:\LiveRadioDFW\liveradiodfw-marketing\.env` (gitignored, hand-created from `.env.example`, never committed). Source of truth for values: 1Password Secure Note "LiveRadioDFW Calendar webhook passphrase." |
| **Commits as** | `LiveRadioDFW <info@liveradiodfw.com>` via HTTPS + Git Credential Manager on the Windows box. |
| **Cost** | Zero Perplexity credits. Runs on local machine. |
| **Manual run** | `cd C:\LiveRadioDFW\liveradiodfw-marketing && python sync_runner.py` |
| **Task registration** | One-time: run `.\setup_sync_task_scheduler.ps1` as Administrator from the repo root (registers the Task Scheduler entry). Re-run if the schedule changes. |
| **Closes** | [bugs.md B7](../bugs.md#b7-webhook-passphrase-and-url-are-publicly-readable-on-the-live-site) (exposure) and [bugs.md B1](../bugs.md#b1-calendar-sync-cron-drifts-across-dst) (DST drift) as a pair. |

### Legacy host (being decommissioned, keep for history + parallel-run window)

| Field | Value |
|---|---|
| **What** | Same as above, but ran the pre-split monolithic `sync_calendar.py` until 2026-04-21. `sync_calendar.py` has since been removed from `gh-pages` (rename → `sync_lib.py`). |
| **Where it runs** | Perplexity `schedule_cron` task named "LiveRadioDFW Daily Calendar Sync" |
| **Owned by** | Perplexity thread "More Band Marketing" (confirmed 2026-04-21 via the Tasks UI). `schedule_cron(list)` returns empty from any other thread — see [bugs.md J1](../bugs.md#j1-scheduled-tasks-are-invisible-across-threads). |
| **When it fires** | 13:11 UTC daily (fixed UTC) — the DST drift bug. |
| **Retire after** | Windows Task Scheduler runs cleanly for 3 consecutive days with identical commit shape. |
| **How to retire** | Open the "More Band Marketing" Perplexity thread → Tasks view → delete the `LiveRadioDFW Daily Calendar Sync` task. Then move this row into "Deleted / defunct tasks" below with a date. |

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

---

## Rules for adding new scheduled tasks

If you (future Jarvis) create a new scheduled task for this project:

1. **Document it here before you leave the thread.** Do not rely on "I'll remember" or "someone will see it in Perplexity's UI." Thread-scoped means invisible the moment the session ends.
2. **Note the owning thread identifier if possible.** Even a short name/date helps the next Jarvis locate it for modification.
3. **Prefer schedules that are DST-safe from the start.** Use Python to convert Central to UTC for the exact month of creation, but also note the drift behavior in this table so someone catches it before winter.
4. **Log the credit cost** if the task runs in Perplexity - it affects Ray's monthly usage.
5. **Cross-link to any bug** that the task is meant to address or any runbook that explains manual equivalents.
