# Marketing Automation

How Live Radio DFW's monthly venue-outreach emails get sent.

## Data Flow (Monthly Availability Email)

```
Band Google Calendar (info@liveradiodfw.com)
         │
         │  Google Calendar API
         ▼
liveradiodfw_availability.py  ──→  availability.json
         │
         ▼
send_availability_email.py
         │
         │  Mailchimp API
         │   1. clone template campaign
         │   2. inject available dates between
         │      <!-- AVAILABILITY_DATES_START --> / END markers
         │   3. send to Venues audience
         ▼
Mailchimp → Venues audience → inboxes
```

## Cadence

- **Trigger:** Windows Task Scheduler runs `run_availability.bat` every Tuesday at 9:00 AM Central
- **Gate:** scripts internally check for "last Tuesday of the month" and exit otherwise
- **Effective cadence:** once per month

## Components (all in [`liveradiodfw-marketing`](https://github.com/TicoRicoRay/liveradiodfw-marketing) repo)

| File | Role |
|------|------|
| `liveradiodfw_availability.py` | Queries band calendar, computes open Fridays/Saturdays for the next 6 months, writes `availability.json` |
| `send_availability_email.py` | Reads `availability.json`, clones Mailchimp template, injects dates, sends to Venues list |
| `run_availability.bat` | Sequential runner for the two scripts; logs to `availability_log.txt` |
| `setup_task_scheduler.ps1` | One-time PowerShell setup to register the Windows Task Scheduler job |
| `email_template_draft.html` | Mailchimp email template with injection markers |
| `new_template.html` | Alternate/newer Mailchimp template |

## Where the scripts actually run

On Ray's Windows box: `C:\Users\myers\Downloads` (path is hardcoded in `setup_task_scheduler.ps1`).

## Blocking logic (what dates are considered "booked")

All blocking flows from the band calendar only. Personal calendars are never queried.

| Event type | Result |
|---|---|
| All-day event (any span) | Block all dates in range (e.g. "Block Kyle Out") |
| Timed event, single day | Block that date (gig) |
| Timed event, 2+ days | Block full range |
| Rehearsal | Ignored |

## Audience & templates in Mailchimp

- **Venues audience ID:** `97cca06eff`
- **Template campaign ID:** `6f64a2aba3` ("March 2026 Availability" draft, used as a cloning source)
- **Mailchimp server prefix:** `us6`
- **API key:** stored in `send_availability_email.py` (line 24) on the local machine — NOT committed to the repo

## Related runbook

- [runbooks/edit-ticket-prices.md](../runbooks/edit-ticket-prices.md) — how to edit ticket prices on the *site* (different system, also backed by the band Google Calendar)

## Why this is a separate repo

`liveradiodfw-marketing` predates the site refactor. It holds the availability automation and marketing assets (style guide, setlist analysis, intro campaign). Keeping it separate from `liveradiodfw-site` keeps operational automation out of the website repo. See [sources-of-truth.md](sources-of-truth.md) for the full repo map.
