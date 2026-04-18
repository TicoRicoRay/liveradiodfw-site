# Sources of Truth

Where each type of data lives. If you're ever confused about where to look or where to edit, start here.

## Shows / Gigs

**Source of truth: Google Calendar owned by `info@liveradiodfw.com`.**

This is a free Google **personal** account on the band domain. The domain's email (MX) is on Microsoft 365; only the Google Calendar side of that account is used for band operations. Confirmed 2026-04-17 by logging in and inspecting the Apps Script project **"LiveRadioDFW Calendar"** under info@.

- Event details (title, venue, date, time, location) live on this calendar
- Ticket prices live in the event **description** (see [runbooks/edit-ticket-prices.md](../runbooks/edit-ticket-prices.md))
- The site (`shows.json` + per-show HTML pages) is derived automatically by `sync_calendar.py` running daily at 8 AM Central, which reads the calendar via the **"LiveRadioDFW Calendar"** Apps Script webhook
- **Never** hand-edit `shows.json` or `shows/*.html` — the sync will overwrite them
- Master copy of the webhook code: [`scripts/LiveRadioDFWCalendar.gs`](../scripts/LiveRadioDFWCalendar.gs). Publish procedure: [runbooks/publish-calendar-webhook.md](../runbooks/publish-calendar-webhook.md)

**rmyers@futurebright.com is NOT the source of truth.** Ray's futurebright account is **subscribed** to info@'s calendar for convenient day-to-day visibility, but it does not own the events. All create/edit/delete operations must target info@'s calendar.

**Not the source of truth:** Outlook calendar. Events may exist there via prior dual-entry habits, but the sync reads from Google only. See [bugs.md](../bugs.md) B3 for the Outlook-originated-event failure mode — always create new events in Google first.

**Never touch:** The EOS calendar (`ray.myers@eosworldwide.com`). It is personal and unrelated to the band. See cardinal rules in the session-startup prompt.

## Venues and Venue Contacts

**Source of truth: Mailchimp**

All venue info, booking contacts, and negotiation history live in Mailchimp:

- Venue names, addresses, websites
- Contact person (name, email, phone, role)
- Booking history and notes
- Negotiation correspondence
- Pay rates, preferences, gotchas

When negotiating a new gig or updating a venue relationship, update Mailchimp — not this repo.

**Why Mailchimp** — it's where the band already tracks mailing list segments and audience data, and it gives a single pane of glass for "who do we know at this venue, when did we last play, what did they pay, what's the follow-up status."

## Band Finances

**Source of truth: (not in this repo)**

Band fees, splits, 1099s, tax records — stored outside this repo. Nothing financial belongs in the public `docs` branch.

## Website Content

**Source of truth: the `gh-pages` branch** of `TicoRicoRay/liveradiodfw-site`

- Static HTML/CSS/JS for liveradiodfw.com
- Updated via GitHub Pages
- Served through Cloudflare (Free plan)
- Nameservers: summer.ns.cloudflare.com + titan.ns.cloudflare.com

## Band-Facing Facts (genre, lineup, songs, positioning, social, bios)

**Source of truth: the public site** at https://www.liveradiodfw.com

If an agent needs to know what the band actually _is_ — genre, era focus, number of vocalists, themed "Station" shows, song count, years together, insurance status, in-ear monitors, tagline, upcoming shows, social handles, mailing list — read the site. The `docs` branch deliberately does not duplicate this content. Treat the site as canonical; if it's not on the site, assume it's not a public fact.

Key pages:
- `/` — hero, positioning, upcoming shows, Stations overview
- `/about` — band identity and history
- `/shows/` — generated per-show pages (see calendar-sync.md)
- `/lander` — merger-announcement landing page for legacy domain traffic

## Scheduled Tasks

**Source of truth: [architecture/scheduled-tasks.md](scheduled-tasks.md)**

Every recurring job that touches the band - what it does, where it runs, when it fires. Perplexity `schedule_cron` tasks are thread-scoped, so this doc is the only durable inventory. If an agent creates a new scheduled task, it must be documented there the same session.

## Documentation

**Source of truth: this `docs` branch** of `TicoRicoRay/liveradiodfw-site`

- Runbooks, postmortems, architecture notes, project plan
- Public — nothing sensitive

## Marketing Automation & Assets

**Source of truth: the [`liveradiodfw-marketing`](https://github.com/TicoRicoRay/liveradiodfw-marketing) repo** (`master` branch)

- Monthly venue-availability email automation (`liveradiodfw_availability.py`, `send_availability_email.py`, `run_availability.bat`, `setup_task_scheduler.ps1`)
- Mailchimp email templates (`email_template_draft.html`, `new_template.html`)
- Marketing style guide
- Setlist/theme analysis
- Merger intro campaign drafts

**Does NOT serve the website.** See [architecture/marketing-automation.md](marketing-automation.md) for the availability-email data flow.

## Repo map

| Repo | Branch | Role |
|------|--------|------|
| `liveradiodfw-site` | `gh-pages` | Live website (liveradiodfw.com) |
| `liveradiodfw-site` | `docs` | This branch — docs, runbooks, postmortems, architecture notes |
| `liveradiodfw-marketing` | `master` | Monthly availability-email automation + marketing assets |
