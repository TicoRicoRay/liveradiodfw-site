# LiveRadioDFW Website
**liveradiodfw.com** — Static website for Live Radio DFW, a 5-piece 80s/90s cover band based in DFW, Texas.

Built April 2026. Deployed on GitHub Pages.

---

## Quick Links
- **Production URL:** https://liveradiodfw.com
- **GitHub repo (website):** https://github.com/TicoRicoRay/liveradiodfw-site (gh-pages branch)
- **GitHub repo (marketing assets):** https://github.com/TicoRicoRay/liveradiodfw-marketing (master only — gh-pages deleted Apr 16)

---

## How It Was Built

Pure static HTML/CSS/JavaScript — no framework, no build tool, no server required. Deployed to GitHub Pages from the `gh-pages` branch.

**Design system:**
- Font: Barlow Condensed (headings), Inter (body) — loaded from Google Fonts
- Primary red: #e63946
- Navy: #1a1a2e
- Pure black nav/footer: #000000
- Dark mode: full support via `data-theme` attribute on `<html>`

**Third-party services:**
| Service | What it does | Account |
|---------|-------------|---------|
| GitHub Pages | Hosts the website | github.com/TicoRicoRay |
| Formspree | Contact/booking forms | mvzdpryd endpoint - delivers to info@liveradiodfw.com |
| Shopify Buy Button | Merch store | Store: 9fvpxk-zd.myshopify.com, Token: 4277e32f2517520413e78a08dd9e793b |
| BandHelper | Song lists (cached) | Account ID: 13881 |
| SimpleTexting | SMS concert alerts | Form ID: 673bc3997cf5d407932e0516 |
| YouTube | Video embeds | @LiveRadioDFW |

---

## Repository Structure

```
liveradiodfw-site/
├── index.html              Home page
├── shows.html              Upcoming shows
├── songs.html              Full song list
├── videos.html             Video page
├── about.html              About the band
├── members.html            Band member bios + photos
├── store.html              Merch store (Shopify)
├── book.html               Booking inquiry form
├── contact.html            Contact form
├── press-kit.html          Media resources
├── corporate-events.html   Corporate event page
├── private-parties.html    Private party page
├── the-all-80s-hits-station.html
├── the-all-70s-no-disco-hits-station.html
├── the-classic-rock-station.html
├── the-all-oldies-hits-station.html
├── nav.html                GLOBAL NAV SOURCE OF TRUTH
├── shows.json              SHOWS SOURCE OF TRUTH
├── build_nav.py            Stamps nav.html into all 16 pages
├── build_shows.py          Stamps shows.json into shows.html + index.html
├── sync_calendar.py        AUTO-SYNC: Google Calendar → shows.json → website (daily cron)
├── build_songs.py          Fetches BandHelper, caches song HTML, stamps into song pages
├── css/
│   └── style.css           Single global stylesheet (bump ?v=N on changes)
├── js/
│   └── main.js             Theme toggle, hamburger menu, show auto-hide
├── img/
│   ├── logo.jpg            Band logo
│   ├── hero.mp4            Hero video (home page)
│   ├── favicon.ico         Favicon
│   └── member-*.jpg        Band member photos
├── cache/
│   ├── songs-all.html      Cached BandHelper song lists
│   ├── songs-80s.html
│   ├── songs-70s.html
│   ├── songs-classic.html
│   ├── songs-oldies.html
│   └── songs-hash.json     MD5 hashes for change detection
├── files/
│   └── 1313292/stage-plot.pdf
└── CNAME                   liveradiodfw.com (for GitHub Pages custom domain)
```

---

## Maintenance Guide

### Adding/Updating/Removing Shows (AUTOMATED)

**Shows are now managed automatically via `sync_calendar.py`.** The Google Calendar (info@liveradiodfw.com) is the source of truth.

**How it works:**
1. A daily cron (8 AM CDT) runs `sync_calendar.py`
2. The script fetches all events from Google Calendar via iCal feed
3. It compares against `shows.json` and:
   - **Adds** new shows found on the calendar
   - **Removes** shows deleted from the calendar
   - **Updates** shows whose details changed (time, venue, address)
4. If any changes are detected, it runs `build_shows.py`, commits, and pushes to gh-pages
5. An email is sent to info@liveradiodfw.com summarizing all changes
6. Deletions trigger a separate alert email (deletions are unusual and may be accidental)

**Manual override:** You can still edit `shows.json` directly and run `python build_shows.py` + push, but changes may be overwritten by the next sync if they don't match the calendar.

**Show entry format in shows.json:**
```json
{
  "date": "2026-MM-DD",
  "day_name": "Sat",
  "day_num": "15",
  "month": "Jun",
  "title": "Venue Name Here",
  "venue": "Full Venue Name",
  "address": "123 Main St, City TX 75000",
  "address_short": "123 Main St, City TX",
  "time": "8:00 PM",
  "maps_url": "https://maps.google.com/?q=Venue+Name+City+TX"
}
```

---

### Updating the Navigation

The nav is defined once in `nav.html` and stamped into all 16 pages automatically.

1. Edit `nav.html`
2. Run: `python build_nav.py`
3. Push all changed HTML files

---

### Updating Song Lists

Song lists are cached from BandHelper. To refresh:

1. Run: `python build_songs.py`
   - If songs changed on BandHelper, it fetches new data and stamps pages
   - If unchanged, it prints "cache hit, skipping"
2. Push changed files

To force a refresh regardless of cache:
```
python build_songs.py --force
```

---

### Changing the CSS

1. Edit `css/style.css`
2. Bump the version number on ALL pages:
   ```
   sed -i 's/style\.css?v=N/style.css?v=N+1/g' *.html
   ```
   (Replace N with current version number)
3. Push

---

### Adding a New Page

1. Copy an existing page (e.g. `contact.html`) as your starting point
2. Update the `<title>`, `<meta description>`, and page-header H1
3. Add the `<!-- BEGIN_NAV -->` / `<!-- END_NAV -->` markers around the nav block
4. Add the new page to `build_nav.py` in the `PAGE_ACTIVE` dictionary
5. Run `python build_nav.py`
6. Push

---

### Pushing Changes

Push to `liveradiodfw-site` only (the `-marketing` repo no longer has a gh-pages branch):

```bash
cd /path/to/liveradiodfw-site
git add -A
git commit -m "Description of change"
git push origin gh-pages
```

---

### DNS (LIVE — completed Apr 16, 2026)

DNS is configured at GoDaddy:

**Apex domain (liveradiodfw.com):**
```
A    @    185.199.108.153
A    @    185.199.109.153
A    @    185.199.110.153
A    @    185.199.111.153
```

**www subdomain:**
```
CNAME    www    ticoricoray.github.io
```

**GitHub domain verification:**
```
TXT    _github-pages-challenge-TicoRicoRay    <value in GoDaddy>
```

**SSL status (as of Apr 16):**
- [x] `https://liveradiodfw.com` — working, valid cert
- [ ] `https://www.liveradiodfw.com` — cert still pending (hourly monitoring cron active)

---

## Scheduled Automation (Crons)

These run automatically via Perplexity Computer:

| Cron | Schedule | What it does |
|------|----------|-------------|
| **Daily Calendar Sync** | **Every day 8 AM CDT** | **Runs `sync_calendar.py` — syncs Google Calendar → shows.json → website. Auto-adds, auto-deletes, auto-updates. Emails info@ on changes. Pushes to gh-pages.** |
| HTTPS Cert Check (temp) | Hourly (until resolved) | Checks `https://www.liveradiodfw.com` cert. Emails info@ on success or after 5 failures, then self-deletes. |

**Calendar sync details:**
- Source of truth: Google Calendar (info@liveradiodfw.com)
- iCal feed URL: private (stored in sync_calendar.py)
- Google Calendar webhook: used for dual-write (create/update events), NOT for sync reads
- Events are dual-written to both Outlook (connector) and Google Calendar (webhook)
- Do NOT add info@liveradiodfw.com as an Outlook event attendee (causes duplicate cross-sync to Google)

---

## Key Credentials (stored separately — do not commit to repo)

| Service | Where to find |
|---------|--------------|
| Shopify storefront token | Context summary / Perplexity memory |
| Formspree endpoint | mvzdpryd — settings at formspree.io |
| SimpleTexting form ID | 673bc3997cf5d407932e0516 |
| Mailchimp API key | liveradiodfw-marketing repo scripts |

---

## Marketing Style Guide

See `MARKETING_STYLE_GUIDE.md` in the `liveradiodfw-marketing` repo (master branch) for:
- Band name formatting rules (LiveRadioDFW camelCase)
- Approved key phrases
- Tone of voice
- What NOT to say
- Consistency checklist

---

## Band Members & Calendar Access

| Member | Role | Email |
|--------|------|-------|
| Ray | Marketing/Website | rmyers@futurebright.com + info@liveradiodfw.com |
| Donna | Social/Events | lady.heavenly77@gmail.com |
| Buck | Guitar | buck.buchanan@verizon.net / buckb5068@gmail.com |
| Kyle | Drums | dcoleman1061@gmail.com |
| Don | Bass | DonMouck@gmail.com |

**Calendar rules:**
- Google Calendar is source of truth for website sync
- All band events must include rmyers@futurebright.com as attendee
- Do NOT add info@liveradiodfw.com as Outlook attendee (causes cross-sync duplicates)
- Do NOT change how band members use the calendar — some are technophobic
