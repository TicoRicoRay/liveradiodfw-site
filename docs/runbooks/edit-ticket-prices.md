# Runbook: Editing Ticket Prices

The band website (liveradiodfw.com) shows a ticket price for each public show. This runbook explains how to change it.

## Source of truth

**The band Google Calendar** (secondary calendar on rmyers@futurebright.com). Ticket prices are parsed from the event **description**.

Do NOT edit `shows.json` or individual show HTML pages by hand — the nightly sync will overwrite them.

## How to set or change a ticket price

1. Open **Google Calendar** in any browser (or the mobile app).
2. Find the event on the band calendar (not the EOS calendar).
3. Open the event and edit the **description**.
4. Add or update a line in this format:

   ```
   Tickets: Free
   ```
   or
   ```
   Tickets: $25
   ```

5. Save.
6. The site updates automatically on the next daily sync (**8 AM CDT**). To push it sooner, run `sync_calendar.py` manually.

## Accepted formats

The parser is case-insensitive and accepts any of:

- `Tickets: Free`
- `Ticket: Free`
- `Tickets: $25`
- `Ticket Price: $15`
- `Tickets: $7.50`
- `Tickets: $1,000` (commas allowed, if you ever need them)

## What happens if you forget

If a public (non-private) event has **no** ticket line in its description, you'll get an alert email at `info@liveradiodfw.com` at the next sync, naming the exact show. The site will show a blank ticket price until you fix it.

## Private events

Events with titles like "Private Event", "Wedding", "Corporate", etc. are marked private by the sync and their ticket price is ignored. No ticket line needed.

## Outlook-native event IDs

If you create an event in **Outlook** and it syncs over to Google Calendar with an Outlook-native hex event ID (a long hex string, no `@google.com` suffix), the Google Apps Script webhook **cannot update** it programmatically. You can still edit it by hand in Google Calendar — just not via automation.

Going forward, prefer creating new events **directly in Google Calendar** to avoid this.

## Editing price rules of thumb

- **Ticket price** = what attendees pay: Free to ~$100
- **Band fee** = what the venue pays us: $400–$3,000 (this is NOT on the website — it stays in your records)

Don't confuse the two.
