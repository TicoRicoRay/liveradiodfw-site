# Windows Task Scheduler — Daily Calendar Sync

> **Canonical runbook has moved.** This file used to hold the install procedure, but as of 2026-04-21 PM the runbook ships alongside the code it installs, in the sibling `liveradiodfw-marketing` repo.

## Read this

- **Canonical install + operate + troubleshoot runbook:** [`liveradiodfw-marketing/docs/windows-sync-task.md`](https://github.com/TicoRicoRay/liveradiodfw-marketing/blob/master/docs/windows-sync-task.md)
- **Code it installs:** [`liveradiodfw-marketing/sync_runner.py`](https://github.com/TicoRicoRay/liveradiodfw-marketing/blob/master/sync_runner.py), [`setup_sync_task_scheduler.ps1`](https://github.com/TicoRicoRay/liveradiodfw-marketing/blob/master/setup_sync_task_scheduler.ps1), [`.env.example`](https://github.com/TicoRicoRay/liveradiodfw-marketing/blob/master/.env.example)
- **Inventory row:** [architecture/scheduled-tasks.md §1 "Daily calendar sync"](../architecture/scheduled-tasks.md)
- **Bug it closes:** [bugs.md B7](../bugs.md#b7-webhook-passphrase-and-url-are-publicly-readable-on-the-live-site)

## Why it moved

Ray's standing architectural preference (2026-04-21, direct quote): _"Rather than download zip files (like a caveman) - can we isolate any sensitive information in a single file - download it. Then everything else is just a pull from github as needed?"_

Consequence: the Windows install runs out of a `git clone` of `-marketing`. Ray `git pull`s for updates; only `.env` is hand-managed locally. The runbook lives with the code so that future updates to either stay lockstep. Duplicating the runbook in two repos would just become two runbooks that drift.

## Quick start (summary — see canonical for full steps)

On Ray's Windows box, one time:

```powershell
cd C:\Tools\LiveRadioDFW
git clone https://github.com/TicoRicoRay/liveradiodfw-marketing.git
cd liveradiodfw-marketing
copy .env.example .env
# Edit .env — fill in the five keys from 1Password "LiveRadioDFW Calendar webhook passphrase"
python sync_runner.py           # smoke test manually
# Run as Administrator:
.\setup_sync_task_scheduler.ps1
```

For updates:

```powershell
cd C:\Tools\LiveRadioDFW\liveradiodfw-marketing
git pull
```

## Why this stub still exists on `-site/docs`

So anyone following a link from `scheduled-tasks.md`, `bugs.md B7`, or any past session note finds a clear pointer instead of a 404. When enough time has passed that all old references are refactored out, this file can go away — or stay, if future agents like the paper trail.
