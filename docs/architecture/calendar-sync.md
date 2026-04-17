# Calendar Sync Architecture

How the band website's shows page gets built and kept in sync.

## Data Flow

```
Google Calendar (band calendar on rmyers@futurebright.com)
         │
         │  POST {action: "list"}
         ▼
Google Apps Script Webhook
         │
         │  returns JSON {events: [...]}
         ▼
sync_calendar.py (runs daily at 8 AM CDT via cron)
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
The band calendar (secondary calendar on rmyers@futurebright.com). Individual events with title, start, end, location, description.

### Google Apps Script Webhook
A webhook that exposes the calendar to `sync_calendar.py`.

- **URL:** not in docs (public branch). See your password manager.
- **Passphrase:** not in docs. See your password manager.
- **Actions:** `list`, `create`, `update`, `delete`
- **Known limitation:** `update` fails on events whose ID is an Outlook-native hex string (events created in Outlook that then synced over). Create events directly in Google Calendar to avoid this.

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
Runs daily at 8 AM CDT. Cron config lives on the server hosting the sync, not in this repo.

## Failure Modes & History

See [postmortems/2026-04-17-sync-wipe.md](../postmortems/2026-04-17-sync-wipe.md) for the incident that led to the non-destructive merge and strict parser.

## How to Run Manually

On the server that hosts the cron:

```bash
cd /path/to/liveradiodfw-site
python3 sync_calendar.py
```

This will fetch fresh calendar data, rebuild `shows.json` and per-show HTML pages, commit, and push to `gh-pages`. The live site updates within ~30–45 seconds.
