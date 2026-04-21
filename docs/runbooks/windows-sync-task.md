# Runbook: Windows Task Scheduler — daily calendar sync

_How Ray installs, operates, and maintains the daily calendar sync on his Windows box after B7 Part 2 moved the runner off `gh-pages`._

This runbook replaces the old Perplexity-hosted `schedule_cron` task that ran `sync_calendar.py` (the monolithic file that exposed the webhook passphrase at `https://www.liveradiodfw.com/sync_calendar.py` until 2026-04-21). The Windows box is the durable host going forward. Ray's Windows box already hosts the monthly availability email (see [architecture/scheduled-tasks.md §2](../architecture/scheduled-tasks.md)); the daily calendar sync now joins it.

---

## What lives where

After B7 Part 2 the sync is split in two halves:

| File | Where it lives | What's in it | Secrets? |
|---|---|---|---|
| `sync_lib.py` | `gh-pages` branch of `liveradiodfw-site`, repo root | Pure functions: `is_gig_event`, `is_private_event`, `parse_ticket_price`, `generate_description_draft`, `calendar_event_to_show`, `check_missing_info`, `detail_diffs`, `merge_calendar_fields`, and the constants they share (`CALENDAR_OWNED_FIELDS`, `SKIP_PATTERNS`, `KNOWN_VENUES`). Safe to publish. | **No** |
| `sync_runner.py` | Ray's Windows box, `C:\LiveRadioDFW\sync\` | Orchestration: loads `.env`, calls the Apps Script webhook, invokes `sync_lib` helpers, regenerates show pages, commits and pushes to `gh-pages`, emails `info@liveradiodfw.com` on missing data. | **Yes** (reads from `.env`) |
| `.env` | Ray's Windows box, `C:\LiveRadioDFW\sync\.env` | `LIVERADIODFW_WEBHOOK_URL`, `LIVERADIODFW_WEBHOOK_PASSPHRASE`, `LIVERADIODFW_REPO_PATH`, plus optional `LIVERADIODFW_ALERT_EMAIL`, `LIVERADIODFW_GIT_BRANCH`, `LIVERADIODFW_GIT_REMOTE`. | **Yes** — never commit. |
| `.env.example` | Ships alongside `sync_runner.py` | Template showing every key with placeholder values. | No |
| Local clone | Ray's Windows box, `C:\LiveRadioDFW\liveradiodfw-site\` (`gh-pages` branch checked out) | The site content the runner edits. `sync_runner.py` imports `sync_lib.py` from here. | Git credential helper only |

Source of truth for the secret values is **1Password Secure Note "LiveRadioDFW Calendar webhook passphrase"** (Ray's standing convention per [runbooks/publish-calendar-webhook.md](publish-calendar-webhook.md)). `.env` on the Windows box is a local cache of those values; if Ray rotates the passphrase, update 1Password first, then `.env`, then redeploy the Apps Script.

---

## First-time install (one-time)

Do these steps once on the Windows box. Expect to hit a couple of minor environment prompts along the way; fix each as it appears rather than trying to validate everything up-front.

### 1. Prerequisites

- [ ] **Python 3.9+** installed and on `PATH`. Confirm with `python --version` in PowerShell.
- [ ] **Git for Windows** installed and on `PATH`. Confirm with `git --version`.
- [ ] `requests` package available to the Python used by Task Scheduler: `python -m pip install requests`.
- [ ] A working `git` identity configured for the `LiveRadioDFW` GitHub account — the runner pushes to `gh-pages` as `LiveRadioDFW <info@liveradiodfw.com>`. Easiest is the **Git Credential Manager** (installed with Git for Windows) authenticated to the `LiveRadioDFW` account, or a dedicated Personal Access Token stored in credential manager.

### 2. Folder layout

Create the folder layout:

```
C:\LiveRadioDFW\
    sync\                     # runner + .env live here
        sync_runner.py
        .env.example
        .env                  # you create this from the template
    liveradiodfw-site\        # repo clone, gh-pages branch
        sync_lib.py
        shows.json
        shows\
        ...
```

Commands (PowerShell):

```powershell
mkdir C:\LiveRadioDFW\sync
cd C:\LiveRadioDFW
git clone https://github.com/TicoRicoRay/liveradiodfw-site.git
cd liveradiodfw-site
git checkout gh-pages
```

### 3. Install `sync_runner.py` and `.env.example`

Ray receives these two files from Jarvis at handoff (see the "Packaging handoff" section at the bottom of this runbook). Drop both into `C:\LiveRadioDFW\sync\`.

### 4. Create `.env` from the template

```powershell
cd C:\LiveRadioDFW\sync
copy .env.example .env
notepad .env
```

Fill in three required values:

- `LIVERADIODFW_WEBHOOK_URL` — from 1Password Secure Note "LiveRadioDFW Calendar webhook passphrase," **Website** field.
- `LIVERADIODFW_WEBHOOK_PASSPHRASE` — from the same Secure Note, **Password** field.
- `LIVERADIODFW_REPO_PATH` — `C:/LiveRadioDFW/liveradiodfw-site` (forward slashes or escaped backslashes; forward slashes read cleaner).

The three optional values default sensibly; leave them commented out unless you need to override.

### 5. Smoke test

```powershell
cd C:\LiveRadioDFW\sync
python sync_runner.py
```

Expected output: webhook list call succeeds, changes (if any) are merged into `shows.json`, per-show HTML pages regenerate, a commit is written locally, and the push to `origin/gh-pages` succeeds (or the runner reports "no changes" cleanly).

If the first run reports "no changes," re-run after adding or editing a test event in Google Calendar to confirm the write path works end-to-end.

### 6. Register with Windows Task Scheduler

Open Task Scheduler → Create Task (not "Create Basic Task"):

- **General:**
  - Name: `LiveRadioDFW Daily Calendar Sync`
  - Run whether user is logged on or not — **unchecked** for a first install (easier to debug). Flip it on once green.
  - Run with highest privileges — unchecked (not needed).
- **Triggers:** New → Daily, start 8:00 AM local, recur every 1 day. Local time is Central; Windows handles DST automatically. This fixes [bugs.md B1](../bugs.md#b1-sync-cron-drifts-by-one-hour-across-dst-change) — the old Perplexity cron was on fixed UTC and drifted an hour every DST flip.
- **Actions:** New → Start a program.
  - Program/script: `python.exe` (full path if not on system PATH, typically `C:\Python39\python.exe` or `C:\Users\myers\AppData\Local\Programs\Python\Python39\python.exe`).
  - Add arguments: `sync_runner.py`
  - Start in: `C:\LiveRadioDFW\sync` (this is what lets the runner find `.env` and the relative `REPO_PATH`).
- **Conditions:** uncheck "Start the task only if the computer is on AC power." Leave "Wake the computer to run this task" unchecked unless the box is regularly asleep at 8 AM.
- **Settings:** check "If the task fails, restart every: 15 minutes," attempt up to 3 times. Uncheck "Stop the task if it runs longer than 1 hour" (the sync is normally under a minute but a slow webhook call can spike).

Save. Windows will prompt for credentials — use Ray's account so the git push uses his credential manager cache.

### 7. Decommission the old Perplexity cron

The old `schedule_cron` task named "LiveRadioDFW Daily Calendar Sync" lives in the Perplexity thread "More Band Marketing." Do not delete it yet. Run the Windows task for **three consecutive days in parallel** with the Perplexity task to confirm the Windows task produces identical commits (same git author, same shape of diff). Once confirmed:

1. Pull up the Perplexity thread "More Band Marketing."
2. Delete the `schedule_cron` task from that thread.
3. Note the removal in [architecture/scheduled-tasks.md](../architecture/scheduled-tasks.md) — move the task from §1 into "Deleted / defunct tasks (for context)" with a date, and add a new §1 pointing at this runbook.

Do **not** skip the parallel-run check. The Perplexity cron burns credits each run but the duplication cost is small versus the risk of a silent gap if the Windows task has an environment issue that only shows up on a cold morning.

---

## Daily operation — normal run

The task runs at 8:00 AM Central every day. No human action required. Artifacts:

- `C:\LiveRadioDFW\sync\sync.log` — rolling log of runs (written by `sync_runner.py`).
- Commits on `gh-pages` signed as `LiveRadioDFW <info@liveradiodfw.com>` via HTTPS + credential manager.
- Emails from `info@liveradiodfw.com` when a show is missing required fields (tickets price, venue address, or start time).

### How to verify last run succeeded

- Task Scheduler → `LiveRadioDFW Daily Calendar Sync` → History tab. Look for "Task completed" with exit code 0.
- Or check the latest commit on `gh-pages`: `git log --author=LiveRadioDFW --oneline -5`.
- Or tail `sync.log`.

### How to force a run

Task Scheduler → right-click the task → Run. Or from PowerShell:

```powershell
cd C:\LiveRadioDFW\sync
python sync_runner.py
```

### How to pause the task

Task Scheduler → right-click → Disable. Re-enable when ready. Useful when the band is in a quiet stretch and Ray is doing hand edits that would fight the auto-sync.

---

## Change procedures

### Rotating the webhook passphrase

1. Rotate in 1Password (new Password field on the Secure Note).
2. Update `C:\LiveRadioDFW\sync\.env` with the new value.
3. Redeploy the Apps Script with the new passphrase — see [runbooks/publish-calendar-webhook.md](publish-calendar-webhook.md).
4. Run `python sync_runner.py` once manually and confirm success before the next scheduled fire.
5. Do **not** put the new passphrase anywhere on `gh-pages`. That's the entire point of B7 Part 2; regressing it is a repeat of the exposure.

### Editing `sync_lib.py` (pure logic change)

1. Make the change on a branch off `gh-pages` in the usual dev flow.
2. Run the repo-root test suite against the updated library (`test_is_private_event.py`, `test_description_handling.py`, `test_cancellation_reschedule.py`) before merging.
3. Merge to `gh-pages`. Ray's Windows box pulls the updated `sync_lib.py` automatically on the next sync run via the `git pull` the runner performs at the start of each execution.

### Editing `sync_runner.py` (orchestration change)

1. Edit the local copy in `C:\LiveRadioDFW\sync\`.
2. Run `python sync_runner.py` manually to confirm.
3. Also copy the new version back to wherever Jarvis keeps the reference copy (see "Packaging handoff" below) so the next install doesn't regress.

`sync_runner.py` is intentionally **not** in the `liveradiodfw-site` repo. If you want a committed reference, put it in a private repo that never becomes public — do not add it to `gh-pages` or the public `docs` branch.

---

## Troubleshooting

**Task runs but nothing commits.** Normal when there are no calendar changes. Check `sync.log` for the "0 diffs" line. Only a problem if multiple days in a row show zero diffs AND you know a show was edited.

**Exit code 1.** Check `sync.log` for the traceback. Most common causes:

- `.env` missing a required key — the runner refuses to start and logs which key.
- Webhook 401 — passphrase drifted between `.env` and the deployed Apps Script. See "Rotating the webhook passphrase" above; both sides must match.
- Webhook timeout — Google Apps Script can be slow. The runner retries once; if both attempts time out, the next scheduled run will catch up.
- `git push` rejected — someone pushed to `gh-pages` between the runner's `git pull` and `git push`. Runner will retry next fire; usually self-heals.

**CDT/CST in alert email body.** That's [bugs.md B17](../bugs.md#b17). Fix is a one-line string constant change in `sync_lib.py` when it gets scheduled.

**Git identity wrong on commit.** Check `git config --global user.name` and `user.email` on the Windows box — must be `LiveRadioDFW` and `info@liveradiodfw.com` respectively for the commit to match historical shape. Fix with `git config --global user.name "LiveRadioDFW"` and `git config --global user.email "info@liveradiodfw.com"`.

---

## Packaging handoff (for Jarvis → Ray)

When Jarvis prepares this install, the handoff consists of exactly three files dropped into a zip or a folder Ray can download:

1. `sync_runner.py` — latest version from the drafting workspace.
2. `.env.example` — template, no real values.
3. This runbook (reference copy; the canonical is at `docs/runbooks/windows-sync-task.md` on the `docs` branch).

Ray walks through sections 1–7 of "First-time install" above and the task is live. Expected wall-clock time including the three-day parallel-run check: roughly half a week elapsed, under 30 minutes of hands-on effort.

---

## Cross-references

- [architecture/scheduled-tasks.md](../architecture/scheduled-tasks.md) — durable cron inventory (gets updated when the Windows task replaces the Perplexity cron).
- [bugs.md B1](../bugs.md#b1-sync-cron-drifts-by-one-hour-across-dst-change) — DST drift bug this runbook closes.
- [bugs.md B7](../bugs.md) — the exposure this runbook's architecture shuts.
- [runbooks/publish-calendar-webhook.md](publish-calendar-webhook.md) — the Apps Script side of the same pipeline.
- [roadmap.md R23](../roadmap.md#r23-preserve-and-document-the-monthly-profile-audit-venue-discovery-cron) — the next job to join this Windows box after the Monthly Profile Audit forensics pass.
