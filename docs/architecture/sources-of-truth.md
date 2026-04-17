# Sources of Truth

Where each type of data lives. If you're ever confused about where to look or where to edit, start here.

## Shows / Gigs

**Source of truth: Google Calendar** (band calendar on rmyers@futurebright.com)

- Event details (title, venue, date, time, location) live on the calendar
- Ticket prices live in the event **description** (see [runbooks/edit-ticket-prices.md](../runbooks/edit-ticket-prices.md))
- The site (`shows.json` + per-show HTML pages) is derived automatically by `sync_calendar.py` running daily at 8 AM CDT
- **Never** hand-edit `shows.json` or `shows/*.html` — the sync will overwrite them

**Not the source of truth:** Outlook calendar (even though the same events exist there via sync). The sync reads from Google only.

**Never touch:** The EOS calendar. It is personal and unrelated to the band.

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

## Documentation

**Source of truth: this `docs` branch** of `TicoRicoRay/liveradiodfw-site`

- Runbooks, postmortems, architecture notes, project plan
- Public — nothing sensitive
