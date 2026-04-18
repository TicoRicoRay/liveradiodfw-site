# Calendar Sync Architecture

How the band website's shows page gets built and kept in sync.

## Data Flow

```
Google Calendar (owned by info@liveradiodfw.com)
         │
         │  POST {action: "list"}
         ▼
Google Apps Script Webhook
         │
         │  returns JSON {events: [...]}
         ▼
sync_calendar.py (runs daily at 8 AM Central via cron)
         │
         ├── parses event description for ticket price
         ├── filters out non-gigs (rehearsals, personal, etc.)
         ├── non-destructively merges into shows.json
         ├── regenerates per-show HTML pages in shows/
         └── git commit + push to gh-pages
         │
         ▼
GitHub Pages serves liveradiodfw.com
```

## Components

### Google Calendar
The band calendar is the **primary** calendar of the free Google personal account `info@liveradiodfw.com`. Individual events with title, start, end, location, description. See [architecture/sources-of-truth.md](sources-of-truth.md#shows--gigs) for the full rationale. rmyers@futurebright.com is **subscribed** (read view) for Ray's day-to-day convenience; it is not the source of truth and must not be used as the target for create/edit/delete.

### Google Apps Script Webhook
A webhook that exposes the calendar to `sync_calendar.py`.

- **Apps Script project name:** `LiveRadioDFW Calendar` (owned by info@liveradiodfw.com, viewable at script.google.com when logged in as info@)
- **Master copy of the code:** [`scripts/LiveRadioDFWCalendar.gs`](../scripts/LiveRadioDFWCalendar.gs) on the `docs` branch. Publishing is manual — see [runbooks/publish-calendar-webhook.md](../runbooks/publish-calendar-webhook.md). The master copy has the passphrase redacted to `'__REPLACE_BEFORE_DEPLOY__'`.
- **URL and passphrase:** kept out of the `docs` branch. **SECURITY ISSUE (B7 — open):** both currently live in `sync_calendar.py` on the `gh-pages` branch, which is public and served at `https://www.liveradiodfw.com/sync_calendar.py`. Remediation pending — see bugs.md B7.
- **Actions:** `list`, `create`, `update`, `delete`
- **Known limitation 1 (B3):** `update` fails on events whose ID is an Outlook-native hex string (events created in Outlook that then synced over). Create events directly in Google Calendar to avoid this.
- **Known limitation 2 (B2):** `update` silently drops attendee modifications. Root cause: `_updateEvent` has no attendee code path. 2-line fix pending — see bugs.md B2.

### sync_calendar.py
Lives in the `gh-pages` branch, runs on the server hosting the cron job (not on GitHub).

**Behavior:**
- **Non-destructive merge** — only overwrites these fields: `date, day_name, day_num, month, title, venue, address, address_short, time, maps_url, private, ticket_price`. Any hand-curated fields (e.g. `description`) are preserved.
- **Strict parsing** — no `Tickets: …` line in description = blank `ticket_price` + alert email (not a silent default to "Free").
- **Alert emails** — sent to `info@liveradiodfw.com` when a public show is missing required info (ticket price, location, etc.), naming the specific show.

### Parser regex
```
r'tickets?(?:\s*price)?\s*:\s*(\$[\d,.]+|free)'
```
Case-insensitive. Matches `Tickets: $25`, `Ticket Price: $15`, `Tickets: Free`, etc.

### Cron
Runs daily at 8 AM Central. Cron config lives on the server hosting the sync, not in this repo.

## Failure Modes & History

See [postmortems/2026-04-17-sync-wipe.md](../postmortems/2026-04-17-sync-wipe.md) for the incident that led to the non-destructive merge and strict parser.

## How to Run Manually

On the server that hosts the cron:

```bash
cd /path/to/liveradiodfw-site
python3 sync_calendar.py
```

This will fetch fresh calendar data, rebuild `shows.json` and per-show HTML pages, commit, and push to `gh-pages`. The live site updates within ~30–45 seconds.
