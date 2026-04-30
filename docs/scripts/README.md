# Do not put automation here

Automation source code (Apps Script `.gs` files, Python scripts, sync
runners, etc.) and their operational runbooks live in the
**liveradiodfw-marketing** repo under `docs/scripts/` and
`docs/runbooks/`.

This `docs/scripts/` directory in **liveradiodfw-site** exists only as
a tombstone for the README you are reading. If you find yourself about
to add a `.gs`, `.py`, `.bat`, or `.ps1` file here, stop. Add it to
liveradiodfw-marketing instead.

## Why

- This repo is the public website. Anything under `docs/` is at risk of
  being served publicly if path filters change. Webhook URLs and
  passphrase-shaped placeholders should never live here.
- Companion code (an Apps Script's Python client, its smoke-test, its
  runbook) lived in two repos at once for several weeks. That split
  caused B41 to take five Apps Script deploys to resolve on
  2026-04-30, because the agent kept directing edits at the wrong copy.
- One canonical location, one source of truth, no diffing required to
  know what is live.

## History

- 2026-04-30: `LiveRadioDFWCalendar.gs` and `publish-calendar-webhook.md`
  were removed from this repo and centralized in liveradiodfw-marketing
  (`master`). See B41 and `docs/postmortems/2026-04-30-b41-availability.md`
  in liveradiodfw-marketing for the full story.
