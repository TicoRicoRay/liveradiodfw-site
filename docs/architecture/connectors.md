# Connectors - Live Radio DFW

_Last updated: 2026-04-17 · 7:54 PM Central_

Every Perplexity external-tool connector on Ray's account, classified by band relevance. This file exists because **connectors are account-wide, not project-scoped** - there is no way in Perplexity today to bind a connector to a specific project. A connected service is visible to every project Ray runs on this account (band, EOS, personal). The cardinal rules in `project-plan.md` substitute for the per-project allow-lists the platform does not provide.

See also [bugs.md J7](../bugs.md) (cross-project contamination risk) and J9 (connectors are account-wide - platform limitation).

## Why this file exists

Same reason as `scheduled-tasks.md`: without a durable inventory, a future Jarvis starting cold will see the connector list and instinctively reach for the wrong one. The most dangerous example is `gcal` (display name "Gmail with Calendar"), which is the EOS identity - using it for band work is a cardinal-rule violation.

---

## 1. Active band use

These have documented band workflows. Runbooks, architecture docs, or scripts reference them directly.

### GitHub (`github_mcp_direct`)
- **Identity:** Ray's personal GitHub (`TicoRicoRay`).
- **Band use:** Read/write both band repos.
  - [`liveradiodfw-site`](https://github.com/TicoRicoRay/liveradiodfw-site): two branches. `docs` (durable memory — this file lives here; never served). `gh-pages` (the live site; also holds `sync_calendar.py` today per B7's exposure note). There is **no** `master` branch on this repo.
  - [`liveradiodfw-marketing`](https://github.com/TicoRicoRay/liveradiodfw-marketing): `master` branch. Availability-email scripts, analysis assets, campaign drafts.
- **Access pattern:** `bash` + `gh` / `git` CLI (credentials pre-configured, never inspect them).
- **Cross-project note:** GitHub will eventually be used by every project Ray runs with Jarvis (durable-memory pattern proven here is being generalized). Band-specific access is via the two repo names above - other projects will have their own repos.
- **Referenced by:** `architecture/calendar-sync.md`, `architecture/marketing-automation.md`, `runbooks/dns-and-pages.md`, `runbooks/end-of-session.md`.

### Mailchimp (`mailchimp__pipedream`)
- **Identity:** Band account (`info@liveradiodfw.com`).
- **Band use:** Source of truth for venue contacts, booking history, and negotiations. Home of:
  - Venues audience `97cca06eff`
  - Monthly availability template campaign `6f64a2aba3`
  - Server prefix `us6`
- **Drives:** Monthly availability email (see `architecture/marketing-automation.md`), R6 merger intro campaign, R7 setlist/theme rollout.
- **Cardinal rule touchpoint:** Venue contacts live here, NOT in the repo. Never copy them into a file.
- **Referenced by:** `architecture/sources-of-truth.md`, `architecture/marketing-automation.md`, `architecture/scheduled-tasks.md`.

### Outlook (`outlook`)
- **Identity:** Band account (`info@liveradiodfw.com`) — Microsoft 365 mailbox (MX on Microsoft 365).
- **Band use:** Inbound venue replies, booking confirmations, business email. **Not the calendar source of truth** (confirmed 2026-04-17: the band's Google Calendar on info@'s free Google personal account is the source of truth; see `architecture/sources-of-truth.md`). Outlook's calendar has historically been a dual-write destination — this habit is under review, see the footnote in `postmortems/2026-04-17-sync-wipe.md`.
- **Cardinal rule touchpoint:** Only the `info@` identity. If a personal Outlook identity shows up here, do not use it for band work.
- **Tools exposed:** `search_email`, `draft_email`, `send_email`, `search_calendar`, `update_calendar`.
- **B4 (calendar host identity) RESOLVED 2026-04-17:** the Google Calendar is owned by info@'s free Google personal account, not by Outlook or a sync bridge. See `bugs.md` fixed-recently section.

### Eventbrite (`eventbrite__pipedream`)
- **Identity:** Band account (`info@liveradiodfw.com`).
- **Band use:** Potential ticketing for public shows. Currently unused in documented workflows - most shows are ticket-free or venue-handled.
- **Status:** Available for band use. No current workflow. Decision pending on whether to adopt for future paid shows.

---

## 2. Available if needed (personal-account utilities)

Connected to Ray's personal Google / Dropbox / etc. account (`rmyers@futurebright.com`). No current band workflow, but fine to use for band if a use case arises. Not EOS - no cross-contamination risk. These are also used by Ray's other personal projects.

### Google Sheets (`google_sheets__pipedream`)
- **Identity:** `rmyers@futurebright.com` (personal).
- **Plausible band use:** Setlist tracking, Station theme/song-coverage matrices, lead pipeline if ever migrated out of Mailchimp, ad-hoc data work. No current workflow.

### Google Docs (`google_docs__pipedream`)
- **Identity:** `rmyers@futurebright.com` (personal).
- **Plausible band use:** Booking-pitch one-pagers, press kits, lyric/arrangement sheets. No current workflow.

### Cloud Convert (`cloud_convert__pipedream`)
- **Identity:** `rmyers@futurebright.com` (personal).
- **Plausible band use:** File format conversion for marketing assets - press-kit PDFs, promo image format conversions, audio format conversions. Ad-hoc utility.

### Dropbox + Files (`dropbox` and `files`) - NOT USED for band work
- **Identity:** `rmyers@futurebright.com` (personal).
- **Split behavior (for context):** Read/search would go through the `files` connector (`search_files_v2`); write/export through the `dropbox` connector (`export_files`).
- **Why not used:** The `dropbox.export_files` tool can only write to the Dropbox root folder - no subfolder targeting. That is too sloppy for band asset management. Docs and durable artifacts live in GitHub (`liveradiodfw-site` docs branch, `liveradiodfw-marketing` repo) instead.
- **Rule:** Do not use Dropbox or Files for band work. If a future Jarvis is tempted to "just drop this in Dropbox," the answer is no - put it in GitHub.

### Spotify (`spotify__pipedream`)
- **Identity:** `rmyers@futurebright.com` (personal).
- **Plausible band use:** Station/setlist research - look up artists' top tracks, audio features (tempo, key, energy) to theme the Stations (All 80s, All 70s No Disco, Classic Rock, Oldies), build reference playlists. Not customer-facing.

---

## 3. Off-limits for band work (cardinal rules)

Using any of these for band work is a cardinal-rule violation. Listed here explicitly so a future Jarvis reading this file sees them flagged rather than reaching for them by name.

### `gcal` ("Gmail with Calendar") - EOS identity
- **Identity:** `ray.myers@eosworldwide.com` (EOS Worldwide - Ray's day job, completely unrelated to the band).
- **Tools exposed:** `search_email`, `draft_email`, `send_email`, `search_calendar`, `update_calendar`.
- **Rule:** **Never read, write, or search this connector for band work.** No exceptions. This is the single biggest cross-project contamination risk on the account - same account, same Perplexity UI, different project. The connector name "Gmail with Calendar" sounds generic and will invite wrong use. It is specifically the EOS calendar and EOS mailbox.
- **If you need email or calendar for the band:** use `outlook` (the band's `info@liveradiodfw.com` mailbox). There is no dedicated band Google Calendar connector today - calendar sync runs through the Apps Script webhook, not a direct connector.
- **Related bugs:** [J7](../bugs.md) (cross-project contamination behaviorally mitigated, not structurally), J9 (platform-level root cause - connectors are account-wide).

### Personal Health Data (`health`)
- **Identity:** Ray's personal EHR data.
- **Rule:** Personal, non-band. Never use for band work. Unlikely to be reached for by mistake, but logged here for completeness.

---

## 4. Not band-relevant (present but unused)

### Amazon Alexa (`amazon_alexa__pipedream`)
Skill-simulation API. No conceivable band use. Leftover from personal experimentation. Not off-limits, just not relevant.

---

## Disconnected connectors (for context)

Currently disconnected on the account - listed so future Jarvis knows they exist and could be connected if needed: Google Workspace Admin, Baserow, Discord, Pipedrive, OneDrive, PandaDoc, Taiga, GitLab, Bitbucket. None have band use cases today.

---

## Rules for adding new connectors

If Ray connects a new service during a band session:

1. **Document it here before the session ends.** Same discipline as `scheduled-tasks.md`. Untracked connectors are how cardinal-rule violations happen.
2. **Note the identity** (which account / email the connector authenticated against). This is the single most important field - it determines whether the connector is band-safe, personal-utility, or off-limits.
3. **Classify into one of the four sections above** (active band use / available if needed / off-limits / not band-relevant).
4. **If the new connector overlaps with an off-limits identity** (new EOS-account connector, for example), add it to section 3 immediately and note the cardinal rule.
5. **Cross-link** to any runbook, architecture doc, or script that uses it.
