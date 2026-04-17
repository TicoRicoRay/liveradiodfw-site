# Scheduled Tasks - Live Radio DFW

_Last updated: 2026-04-17_

Every scheduled/recurring job that touches the band, where it runs, what it does, and how to find or modify it. Nothing automated should exist off this list - if a future agent creates a new scheduled task, add it here the same day.

## Why this file exists

Perplexity `schedule_cron` tasks are **thread-scoped**. A task created in thread A is invisible from thread B, even to the same account. Running `schedule_cron(list)` in a new thread returns an empty array even when tasks are actively firing elsewhere. That's how we spent half of 2026-04-17 AM hunting for a daily sync that nobody in the active thread could see. This file is the only durable inventory.

---

## 1. Daily calendar sync

| Field | Value |
|---|---|
| **What** | `sync_calendar.py` runs end-to-end: calls Apps Script webhook → parses ticket prices from event descriptions → non-destructively merges into `shows.json` → regenerates per-show HTML pages → git commit + push to `gh-pages` → emails `info@liveradiodfw.com` on missing data |
| **Where it runs** | Perplexity `schedule_cron` task |
| **Owned by** | Unknown prior thread (NOT this one). `schedule_cron(list)` returns empty here. |
| **When it fires** | 13:11 UTC daily (fixed UTC) |
| **Effective local time** | 8:11 AM Central in summer, **7:11 AM Central in winter** - this is the DST drift bug |
| **Commits as** | `LiveRadioDFW <info@liveradiodfw.com>` via HTTPS + PAT, unsigned |
| **Cost** | Burns Perplexity credits per run |
| **Bug filed** | [bugs.md B1](../bugs.md) - DST-unsafe schedule |
| **Manual run** | `cd /path/to/liveradiodfw-site && python3 sync_calendar.py` on the server that hosts the cron (which we don't have) - in practice, run manually from whichever thread you're in, or ping the webhook directly |

### How to find the owning thread

1. Open Perplexity in-app
2. Go to scheduled tasks / cron view
3. Look for a task named something like "LiveRadioDFW calendar sync" or "daily sync"
4. Note the thread that owns it and document here

### How to fix the DST drift

Once the owning thread is found:
1. From that thread, call `schedule_cron(action="update", cron_id=..., cron=<Central-aware expression>)` using Python to convert Central → UTC properly
2. Verify the next firing time looks right for Central (8:00 AM year-round)
3. Document the owning thread name + task ID in this file

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
