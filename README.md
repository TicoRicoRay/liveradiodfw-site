# LiveRadioDFW Website
**liveradiodfw.com** — Static website for Live Radio DFW, a 5-piece 80s/90s cover band based in DFW, Texas.

Built April 2026. Deployed on GitHub Pages.

---

## Quick Links
- **Staging URL:** https://ticoricoray.github.io/liveradiodfw-marketing/
- **Production URL:** https://liveradiodfw.com (after DNS cutover)
- **GitHub repo (website):** https://github.com/TicoRicoRay/liveradiodfw-site
- **GitHub repo (marketing scripts):** https://github.com/TicoRicoRay/liveradiodfw-marketing

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

### Adding a New Show

1. Edit `shows.json` — add a new entry in this format:
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
2. Run: `python build_shows.py`
3. Push: `git add shows.json shows.html index.html && git commit -m "Add show: Venue Date" && git push origin gh-pages`

The script automatically sorts by date and stamps both `shows.html` and `index.html` (home page shows 3 upcoming).

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

Always push to BOTH repos:

```bash
# 1. Marketing repo (staging)
cd /path/to/liveradiodfw-site
git add -A
git commit -m "Description of change"
git push origin gh-pages

# 2. Site repo (production after DNS cutover)
cd /path/to/liveradiodfw-site-deploy
rsync -a --exclude='.git' /path/to/liveradiodfw-site/ .
git add -A
git commit -m "Sync: description"
git push origin gh-pages
```

---

### DNS Cutover (when ready to go live)

The `CNAME` file already contains `liveradiodfw.com`. Set these DNS records at your registrar:

**For apex domain (liveradiodfw.com):**
```
A    @    185.199.108.153
A    @    185.199.109.153
A    @    185.199.110.153
A    @    185.199.111.153
```

**For www subdomain:**
```
CNAME    www    ticoricoray.github.io
```

After DNS propagates (15 min - 48 hrs), GitHub Pages will automatically provision SSL.

**Post-cutover checklist:**
- [ ] Add `liveradiodfw.com` to SimpleTexting allowed domains (if required)
- [ ] Submit sitemap to Google Search Console: https://liveradiodfw.com/sitemap.xml
- [ ] Update Google Business Profile website URL
- [ ] Update Mailchimp campaign links from staging URL to liveradiodfw.com
- [ ] Update Formspree confirmation message (currently generic)
- [ ] Set up Cloudflare in front of GitHub Pages for cache control

---

## Scheduled Automation (Crons)

These run automatically via Perplexity Computer:

| Cron | Schedule | What it does |
|------|----------|-------------|
| Show Calendar Check | Every Monday 10am CDT | Checks band calendar vs shows.json, flags missing shows |
| Availability Check Reminder | Every Tuesday 9am CDT | Reminds Ray to check availability output on last Tuesday of month |
| Pre-Send Warning | Sat day 22-28 9am CDT | Warning before monthly Mailchimp availability send |
| Monthly Setlist Review | First Saturday 10am CDT | Reviews BandHelper setlist for new theme opportunities |
| Monthly Venue Discovery | First Saturday 9am CDT | Searches for new DFW venues, adds to Mailchimp |

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

See `MARKETING_STYLE_GUIDE.md` in the `liveradiodfw-marketing` repo for:
- Band name formatting rules (LiveRadioDFW camelCase)
- Approved key phrases
- Tone of voice
- What NOT to say
- Consistency checklist
