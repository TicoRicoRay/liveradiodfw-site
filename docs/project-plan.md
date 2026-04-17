# Live Radio DFW — Project Plan

_Last updated: 2026-04-17_

## Open items

### 1. Migrate old band domains off Bandzoogle (BLOCKS Bandzoogle cancellation)
Bandzoogle Domain Manager shows 3 domains currently attached:
- `liveradiodfw.com` (PRIMARY) — **already moved** to Cloudflare → GitHub Pages
- `jacksoncrossingdallas.com` — still pointed at Bandzoogle
- `riskybusinessdfw.com` — still pointed at Bandzoogle

**Action:**
- Add both old domains as sites in Cloudflare (same nameserver swap pattern as liveradiodfw.com)
- Create Cloudflare Bulk Redirects (or Page Rules) sending all traffic to `https://www.liveradiodfw.com/lander`
- Remove both domains from Bandzoogle Domain Manager
- Then cancel Bandzoogle subscription

### 2. Wildcard 301 for other cached URLs (non-`/home`, non-`/lander`)
Google has cached individual old show pages.

**Recommendation: Cloudflare Bulk Redirects (Free plan)**
- Free plan allows one redirect list, up to 20 redirects
- Can pattern-match known old paths → `/` (homepage) or `/shows`
- Preserves link equity; eliminates soft 404s
- Alternative: Single catch-all Page Rule `liveradiodfw.com/*show*` → `/shows` (Free plan has 3 page rules)

**Status:** Deferred until we pull the full list of cached URLs from Google Search Console.

### 3. Historic shows migration (SEO)
Bandzoogle staging (https://liveradiodfw.bandzoogle.com) plus The Bash profile still hold the historical show archive. Migrate them into `/shows/` as permanent pages for long-tail SEO and credibility.

**Action:**
- Pull show history from Bandzoogle staging calendar
- Pull show history from The Bash profile
- Generate one static page per historical show (same template as current shows)
- Add to sitemap.xml

### 4. Google Search Console cleanup
- Submit updated sitemap.xml
- Request re-indexing of `/home` redirect + `/lander`
- Use URL inspection to force refresh on cached dead URLs

## Recently completed

### 2026-04-17
- ✅ Site back online via Cloudflare → GitHub Pages
- ✅ `/lander` page built from Bandzoogle staging copy (merger announcement) + hero image
- ✅ `/home` meta-refresh redirect to `/` (covers Google-cached /home URL)
- ✅ OG Cellars ticket price restored ($25)
- ✅ Grandfathered "Tickets: Free" into Google Calendar for all 7 public non-OG-Cellars shows
- ✅ Watters Creek 6/6 manually updated in Google Calendar UI (webhook can't touch Outlook-native IDs)
- ✅ `sync_calendar.py` patched:
  - Non-destructive merge (preserves hand-curated fields like `description`)
  - Strict ticket-price parser (blank + alert instead of silent "Free")
- ✅ Dry-run verification: 10 shows, 10 events, 0 drift, 0 alerts
- ✅ Postmortem written (Chapter 2: Apr 16-17 outage + Cloudflare fix, plus sync-wipe incident)
- ✅ `docs` branch established on `liveradiodfw-site` repo

## Architecture notes

- **Shows / gigs:** Google Calendar is the source of truth. See [architecture/calendar-sync.md](architecture/calendar-sync.md).
- **Venues + contacts:** Mailchimp is the source of truth (negotiations, booking history, contact info). See [architecture/sources-of-truth.md](architecture/sources-of-truth.md).
- **Website content:** `gh-pages` branch of this repo.
- **Docs:** `docs` branch of this repo (where you are).
