# Live Radio DFW - Roadmap

_Last updated: 2026-04-23 AM (R26 filed and shipped: Cloudflare cache purge tool; R25 Part A shipped earlier same session; R23 filed to preserve the Monthly Profile Audit venue-discovery cron; R22 filed 2026-04-19 from /lander smell-test; R19 shipped, R14 enriched, R4/R19/R20/R21 filed earlier from GSC audit)_

Future plans, grouped by theme. Things we've decided or want to do but haven't scheduled.

For live defects, see [bugs.md](bugs.md). For session-to-session handoff and "pick up here next time", see [project-plan.md](project-plan.md).

---

## How to add a roadmap item (READ BEFORE ADDING)

### 1. This list is for PLANNED WORK only

Not defects. Not urgent patches. If it's broken, it belongs in [bugs.md](bugs.md) with a **B** prefix (or **J** if it's a Jarvis limitation). If it's something Ray wants to discuss before deciding, it belongs in [project-plan.md](project-plan.md) under "Pending discussion" with a **D** prefix.

### 2. Pick the next sequential R number

Scan all existing `### R<n>.` headings in this file, find the highest number, add 1. No reuse, no skipping.

### 3. Use this entry template

```
### R<n>. <Short title, no period>

<1-3 sentences of context: what's the goal and why.>

**Plan:** (or **Action:** / bullet list of steps)

**Depends on:** Anything that must happen first. "None" is valid.

**Priority:** High / Medium / Low / Parked.
```

Group under the right theme heading (Ops / infrastructure, SEO / content, Marketing automation, Decisions pending, Parked / someday-maybe). Create a new theme section only if the item genuinely doesn't fit an existing one.

### 4. Commit message format

```
docs: add R<n> - <short title>
```

### 5. After adding

- Commit to the `docs` branch, push
- Reply to Ray with the R ID and commit link
- If this item is high-priority and actionable now, also mention it in the "Top priorities right now" list in [project-plan.md](project-plan.md)

---

## Ops / infrastructure

### R1. Cancel Bandzoogle subscription ~~[OPEN]~~ &rarr; **DONE 2026-04-18**
Both legacy domains (`jacksoncrossingdallas.com`, `riskybusinessdfw.com`) are already Cloudflare-redirected to `/lander`. Remaining work (all completed):
- ~~Remove both domains from Bandzoogle Domain Manager (if still listed)~~
- ~~Cancel the Bandzoogle plan~~
- ~~Verify redirect rules land on `https://www.liveradiodfw.com/lander` (HTTP 301)~~

**Closed 2026-04-18:** Ray closed the Bandzoogle account. Recurring subscription cost eliminated. Legacy-domain redirects to `/lander` were already in place via Cloudflare before cancellation; no infra change required on our side. If either legacy domain ever drops out of DNS control, `/lander` is still the canonical merger-announcement landing and can be pointed at from any new source.

**Priority:** ~~High - recurring subscription cost is the motivator.~~ N/A (closed).

### R2. UptimeRobot monitoring ~~[OPEN]~~ → **DONE 2026-04-19**
Set up UptimeRobot (free tier) for `https://www.liveradiodfw.com` with SMS + email alerts. Was a checkbox in the DNS/Pages runbook but not provisioned. Catches outages like the 2026-04-15 event faster than Google Search Console noticing.

**Closed 2026-04-19:** UptimeRobot free-tier HEAD-request monitor on `https://www.liveradiodfw.com`, 5-minute polling interval. Alerts route to `info@liveradiodfw.com`, which pushes to Ray's phone and Apple Watch in real time. Dashboard is password-protected. Free tier is HEAD-only — keyword monitoring (which would catch soft failures like blank body / JS error served with a 200) requires GET and is a paid-tier feature, intentionally skipped. API + connector options exist for future integrations (Slack/Discord feed, on-site status strip) but are intentionally unused; the email path is sufficient for a low-traffic marketing site. Monitor has been live and stable for several days prior to formal close-out.

**Priority:** ~~Medium. Low effort.~~ N/A (closed).

### R11. Extend `build_includes.py` to cover head-level snippets

**Why:** The site is about to grow from ~15 top-level pages to many more (R5 historic-show migration alone will add dozens of individual show pages, and we have ongoing plans for more SEO/landing pages). Today `build_includes.py` owns nav and footer as single points of maintenance via `<!-- BEGIN_NAV -->` / `<!-- BEGIN_FOOTER -->` markers, but the inline `<head>` script (theme bootstrap, and soon anything else we want uniform across the site) is still hand-copied into every `.html` file and also generated inline inside `build_show_pages.py`. Every new page Ray adds is a fresh copy of head content that can drift. Every fix to that content (like B12, the theme-persistence bug) means touching 15+ files.

**Scope:** Add a third include marker pair `<!-- BEGIN_HEAD_BOOT -->` / `<!-- END_HEAD_BOOT -->` served from `includes/head-boot.html`. Move the theme bootstrap there as the first tenant. Reuse the same pattern for future head-level content we want consistent site-wide (cache-bust version string, analytics snippet if we ever add one, shared meta defaults, favicon block, preload/preconnect hints).

**Also:** Update `build_show_pages.py` to read from the same `includes/head-boot.html` instead of inlining its own copy of the bootstrap script, so show-detail pages and top-level pages stay in sync.

**Priority:** High-leverage, low-effort. Worth doing **before** B12's fix lands so the B12 patch is a single-file edit to `includes/head-boot.html` instead of a 15-file sweep. Also makes future template-level bugs ("add viewport tag to all pages", "update cache-bust v=") similarly trivial.

**Depends on:** Nothing. Can ship standalone.

---

### R3. Google Search Console cleanup ~~[OPEN]~~ → **DONE 2026-04-19**
- ~~Submit updated `sitemap.xml`~~
- ~~Request re-indexing of `/home` redirect + `/lander`~~
- ~~URL-inspection sweep of cached dead URLs to force refresh~~

**Closed 2026-04-19:**

1. **Sitemap** submitted and read by Google. Current count: 112 URLs (17 top-level + 95 show pages post R5/R16 import). Google is working through the backlog; first-crawl of the new pages expected within 1–7 days.
2. **`/lander`** live-tested in Search Console, confirmed indexable, re-indexing requested 2026-04-19. Same for `/home` originally but see #3.
3. **`/home` handled differently than planned.** The original plan assumed `/home` was a redirect that needed re-indexing. It was actually a duplicate of the home page served at a second URL (GitHub Pages extensionless routing of `home.html`), created earlier specifically because Google had cached `/home` from the old Bandzoogle site. Search Console confirmed `/home` is no longer in Google's index, meaning the legacy cached URL problem for `/home` is already solved. Replaced the duplicate-content scaffolding with a proper Cloudflare Page Rule 301: `*liveradiodfw.com/home*` → `https://www.liveradiodfw.com/` (301 Permanent Redirect). Verified with curl against every realistic variant (apex/www, trailing slash, `.html`, query string, case variants) — all return 301 to the canonical root, and `/`, `/shows`, `/about` stay 200. See [dns-and-pages.md](runbooks/dns-and-pages.md#cloudflare-page-rules) for the rule config.
4. **URL-inspection sweep of cached dead URLs** is rolled forward into R4 (which always covered this territory via wildcard redirects). R4 can now be evaluated against current GSC 404/redirect-error counts rather than a stale cached-URL export. Reassess 2026-05-03 after Google has had ~2 weeks to crawl the post-R5/R16 state.

**Follow-up:** ~~`home.html` still exists in the `gh-pages` repo as a duplicate of `index.html`.~~ **Done 2026-04-21 (B25):** `home.html` deleted from the repo. The Cloudflare Page Rule remains in place as belt-and-suspenders insurance against any external inbound links to `/home` or `/home.html`.

**Priority:** ~~(not scored)~~ N/A (closed).

---

## SEO / content

### R4. Wildcard 301s for cached URLs
Google has cached individual old show pages and legacy Bandzoogle URL patterns. Cloudflare Bulk Redirects (Free plan: one list, up to 20 redirects) pattern-match known old paths → `/` or `/shows`. Alternative: single catch-all Page Rule `liveradiodfw.com/*show*` → `/shows`.

**Depends on:** ~~R3 (need the cached-URL list from Google Search Console first).~~ R3 closed 2026-04-19; cached-URL inventory now available programmatically via the `google_search_console__pipedream` connector.

**Concrete URL patterns still in Google's index (GSC audit 2026-04-19, last 28 days):**

1. **`.html` Bandzoogle variants** (low-volume but index-budget waste, position 1 for exact-match so Google treats them as canonical for direct lookups):
   - `/book.html` (6 imps), `/contact.html` (2), `/corporate-events.html` (6), `/members.html` (6), `/press-kit.html` (2), `/private-parties.html` (6)
   - **Partially mitigated 2026-04-21 (B25):** every page now emits `<link rel="canonical" href="https://www.liveradiodfw.com/<slug>">` (no `.html`) and the sitemap lists only extensionless URLs. Google will consolidate the `.html` variants onto the canonical on its own schedule. Cloudflare wildcard 301s still worth doing for immediate redirect at the edge (avoids relying on Google to re-crawl), but lower urgency now. Single wildcard `*.html` → strip-extension, or per-path list (6 entries fits well under the 20-rule Cloudflare free plan limit).
2. **Bandzoogle event-URL pattern** `/event/<id>/<id>/<slug>` (zombie URLs from pre-migration era):
   - Observed: `/event/5710250/691552668/live-radio-all-80s-hits`, `/event/5900541/707881016/fresh-by-brookshires-fate-tx`, `/event/5900542/...`, `/event/6055650/...`, `/event/6100957/...`, `/event/6364768/...`, `/event/6378412/...`, `/event/6379565/...` (8 distinct event URLs, 18 total imps)
   - Fix: single wildcard `*liveradiodfw.com/event/*` → `https://www.liveradiodfw.com/shows` (one rule).
3. **`http://` (non-HTTPS) variants in the index** — `http://liveradiodfw.com/` still showing 20 impressions despite Cloudflare serving HTTPS. Cloudflare is correctly redirecting at request time, so this is cosmetic index-freshness lag, not a live defect. Worth confirming the edge redirect is **301 not 302** (belt-and-suspenders — 302 would preserve HTTP as canonical in Google's eyes).
4. **`/home` already handled** (R3 2026-04-19 Cloudflare Page Rule). Traffic was 143 imps / 17 clicks (61% of site clicks) pre-301, so R4 consolidation onto `/` is operating on a larger surface than we assumed. See R21.

**Priority:** Medium. Reassess 2026-05-03 after Google re-crawls. The concrete patterns above suggest 2-3 wildcard rules would cover ~90% of zombie index volume — well within the Cloudflare free-plan 20-rule ceiling.

### R5. Historic shows migration ~~[OPEN]~~ ~~[IN PROGRESS]~~ → **SHIPPED 2026-04-18 PM**
Bandzoogle staging (`https://liveradiodfw.bandzoogle.com`) and The Bash profile still hold the full historical show archive. Migrate into `/shows/` as permanent pages for long-tail SEO and credibility.

**Bandzoogle scope (confirmed 2026-04-18 via browser extract):**
- **33 past shows** across 2 pages: page 1 (20 shows, Apr 11 2026 → May 2 2025) + page 2 (13 shows, Apr 5 2025 → Aug 9 2024)
- Shows span ~20 months. Oldest is Aug 9 2024 at Harvest Hall Grapevine
- 4 shows from Aug-Sep 2024 are from the **Jackson Crossing** era (prior band name), caught via description text mentioning "Jackson Crossing"; we'll regenerate those descriptions via B16 draft path so they land with current voice rather than preserving the prior brand references
- 5 descriptions are truncated at ~95 chars by Bandzoogle's HTML with no "Read more" expansion available
- No ticket prices were recorded on Bandzoogle (not shown on any of the 33 past shows)

**Plan (this session, 2026-04-18):**
1. **Import layer (one-time):** new `lrdfw-ghpages/import_bandzoogle.py`. Reads the 33 shows, normalizes venue names against existing shows.json conventions (e.g. `"Fresh by Brookshires - Fate TX"` → `"FRESH by Brookshire's"`), extracts actual venue from address when the title is a marketing slogan, parses the actual venue address, sets `"past": true` + `"source": "bandzoogle-import-2026-04-18"`. Dedupes against any existing shows.json dates.
2. **Description strategy per B16 rollout:**
   - Bandzoogle description present and >= 50 chars and not truncated → use verbatim
   - Bandzoogle description missing, truncated, or mentions "Jackson Crossing" → B16 `generate_description_draft()` with `[DRAFT - ...]` flag; page renders placeholder until Ray approves
   - Private events → no description, same as current (handled naturally)
3. **Build layer:** extend `build_shows.py` to split shows into upcoming + past, stop rendering past on `/shows` and home; extend `build_show_pages.py` to render a subtle "Past show" banner and no Add-to-Calendar / Get-Directions CTAs (irrelevant for past shows).
4. **New index page:** `past-shows.html` (new file, built via a new builder) — reverse-chronological list of past shows, same card style as `/shows`. Linked from `/shows` and footer.
5. **Sitemap:** append all 33 past-show pages to `sitemap.xml`.
6. **Review gate:** after import + build generate local preview, pause and present the full list to Ray for batch approval BEFORE committing to gh-pages.

**The Bash profile (deferred, not this session):** a separate R-entry will be filed when we tackle that source.

**Priority:** Medium. Good for long-tail SEO and credibility. Blocking follow-up: description enrichment work will continue after the initial batch ships; high-value venues (repeat bookings, marquee shows) get hand-curated replacements over time.

**Status:** SHIPPED 2026-04-18 PM — 33 Bandzoogle shows live at https://www.liveradiodfw.com/past-shows.html. Commit `51da273` on gh-pages. Shipped breakdown: 22 verbatim (with prior-band-name sanitization), 6 machine-draft placeholders, 5 private events. Per Ray: shipping best-guess state and iterating on any that look off. Older-than-Bandzoogle shows (2021-2024) to be added as Ray digs them up — follow-up import will re-use `import_bandzoogle.py` with a fresh raw file.

**Follow-ups:**
- Thin Lion & Crown boilerplate descriptions (5 shows, ~62 chars each, near-identical) are good candidates for hand-curated rewrites if Ray wants more SEO depth on those pages.
- Next import batch: older shows Ray surfaces (pre-Aug 2024). Same script, new `bandzoogle_raw.json` (or analogous).

### R16. Historic calendar import (pre-Bandzoogle 2021–2024) → **SHIPPED 2026-04-18 PM**
63 past shows imported from the `info@liveradiodfw.com` Google Calendar covering 2021-04-16 through 2024-07-27 (all pre-date the R5 Bandzoogle earliest entry of 2024-08-09, so zero dedupe collisions). Shipped via new `import_historic.py` + `build_approved_historic.py` in the gh-pages repo.

**Breakdown:** 59 public + 4 private. All 59 public entries carry `[DRAFT - ...]` machine descriptions (internal calendar notes — booking fees, gate codes, contact numbers — are never shipped verbatim). Public pages render the "Show details coming soon" placeholder until Ray enriches them. shows.json grew 43→106; show pages 36→95; sitemap regenerated via new `update_sitemap.py`. Commit `100d182` on gh-pages.

**New canonical venues registered:** Plano Sports Tavern, The Maverick, American Legion Post 597, Howling Mutt Brewing, Lava Cantina The Colony, Turning Point Beer, Johnny Krackers, Harry Myers Park, Horsemen's Bar-B-Que, The Village Dallas, Shakertins Prosper, Rockin' S at Twin Coves.

**Follow-ups:** enrichment passes for the 59 placeholder pages, ideally grouped by venue (all Frisco Bars, all Lion & Crowns, etc.) for speed.

### R17. Upgrade calendar icons across the site
Replace the current calendar-date chips on the homepage, `/shows`, `/past-shows`, individual show pages, and future locale pages (see R18) with a polished HTML+CSS calendar-icon treatment inspired by [SitePoint's "Create a Calendar Icon in HTML5 and CSS3"](https://www.sitepoint.com/create-calendar-icon-html5-css3/) — month band across the top, large day number body, subtle dashed perforation, layered page-stack shadow for depth. Match our palette (B14 red-on-black dark mode + light-mode counterparts) instead of SitePoint's orange.

**Pattern from the reference (palette-swap target in parens):**
- Outer card: white bg (dark mode: `--surface`), rounded corners, multi-layer `box-shadow` stack for 3D page/binding effect
- Month band: top strip, solid fill (`--red`) with white text, dashed bottom border for the perforated-torn-edge look
- Day number: oversized (2.8em equivalent), dark text on light (light text on dark)
- Day name: small, bottom, in accent color
- All ems/percentages so it scales with `font-size` on the container

**Scope:**
- Audit every place a date pill renders today: `build_shows.py` full cards, compact cards, past-show cards, `show-page-meta` on individual show pages, home hero upcoming-shows strip.
- Build one reusable CSS component (`.cal-icon` with `.cal-icon__month`, `.cal-icon__day`, `.cal-icon__dow`) in `style.css` with light + dark theme variants.
- Update all builders/templates to emit the new markup. Bump `style.css?v=`.
- Verify in both palettes via `screenshot_page`.
- Accessibility: semantic `<time datetime="YYYY-MM-DD">` wrapper with `aria-label` like "Friday, July 23, 2021".

**Priority:** Medium. Visual polish, not critical path. Good candidate after a batch of placeholder descriptions get enriched (R16 follow-up) so the upgraded icons sit alongside real copy instead of placeholders.

### R19. `/lander` conversion audit ~~[OPEN]~~ → **SHIPPED 2026-04-19 AM**

**Shipped 2026-04-19** — [commit `043866c`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/043866c) (and prior [commit `eae3ad8`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/eae3ad8)). Lives at [liveradiodfw.com/lander](https://www.liveradiodfw.com/lander).

**What changed:**
- Title: `Risky Business DFW & Jackson Crossing are now Live Radio DFW` → `Live Radio DFW - Dallas-Fort Worth Tribute & Cover Band for Hire`. SERP-visible line now signals booking intent, geography, and the tribute/cover dual framing (venue-booker + party-planner) instead of two legacy band names.
- Meta description: `DFW tribute & cover band performing themed shows to the 80s, 70s, classic rock, and oldies eras. 100+ songs, 5 vocalists, fully insured. Weddings, corporate, private.` — 154 chars, commercial-intent first.
- H1: `We're Now Live Radio DFW` → `Dallas-Fort Worth Tribute & Cover Band for Your Next Event`.
- Opening paragraph: booking-intent lede, tribute-shows-to-eras-not-artists framing (MTV 80s, free-form 70s rock, classic rock radio canon, oldies songbook), self-updating copy ("book an individual themed Station, or mix several together") so future Station additions don't require a copy fix.
- New H2 `Our Themed Tribute Shows` over the existing Stations block (reframes them as tribute products, not a merger explainer).
- New H2 `Custom Tribute Shows` presents three ready-to-book named products (A Tribute To MTV, Graduation Night, Texas Music Night) framed as reader-facing value rather than internal positioning. First draft used memo-speak ("versatility is what we offer, marketable theming is what the nicer venues want, we bridge the two") and Ray flagged that it was tuned for our internal conversation, not for venue buyers or party planners. Final copy opens reader-side ("some events call for more than a standard cover-band set") and translates "marketable theming" into buyer language ("a show with a theme — something you can promote, something with a hook"). See R14 for the full final copy and craft notes.
- Merger section preserved but retitled `From Risky Business DFW and Jackson Crossing` and moved below the fold — still owns bookmark-search traffic (Risky Business DFW / Jackson Crossing name queries) without burying commercial intent above it.
- CTA: three equal-weight buttons (Book / Shows / Homepage) → single primary (Book Live Radio DFW) + ghost secondary (See Upcoming Shows). Homepage button removed — visitor is already on a band page, homepage is a lateral move that dilutes intent. Aligns with `-marketing` Section 11 one-primary-CTA guideline.

**Philosophy notes for future SEO/copy work:**

1. **Honesty drove framing, not the other way around.** The band performs themed tribute shows (to eras, moments, cultural audiences) but is not a tribute act in the single-artist sense. That nuance became a sales advantage instead of a liability.
2. **Audience-check every paragraph twice:** once for the copywriter's intent, again for each intended reader's seat. The first Custom Tribute Shows draft passed my internal check but failed Ray's audience check — words that worked between us ("nicer venues," "we bridge the two") read wrong in front of actual venues and planners. Reuse this pattern when other pages get the same treatment: draft, then re-read from each audience's seat before shipping.
3. **Demonstrate positioning through products, don't announce it.** The final Custom Tribute Shows paragraph doesn't say "we bridge cover-band flexibility and tribute-show theming" — it shows the bridge by putting the named-show menu in front of the reader. Rule of thumb: if a sentence narrates our strategy ("versatility is what we offer"), rewrite it to either demonstrate the strategy or cut it.

**Re-indexing:** `submit-url-for-indexing` via the Pipedream connector returned null. Google's Indexing API is officially limited to `JobPosting` and `BroadcastEvent` schema types; non-matching URLs get silent no-ops. Filed as a connector limitation in `architecture/connectors.md`. The actual path to re-indexing for band URLs is either (a) wait for Google's normal re-crawl cadence or (b) Ray uses GSC's URL Inspection tool "Request indexing" (a separate mechanism that does work for arbitrary URLs). Recommended: Ray request re-index from GSC UI when convenient, or let natural re-crawl run.

**Measurement plan:** GSC comparison window 2026-04-19 (baseline) vs 2026-05-17 (~4 weeks post-deploy). Key metrics to watch on `/lander`:
- CTR on `dallas cover bands`, `cover bands in dallas`, `80s cover band dallas`, `dfw cover bands`, `live bands for events in dfw` — these are where the CTR lift should show up if the title/meta rewrite worked.
- Average position on the above queries (secondary, slower to move, expected to drift positive as CTR engagement improves).
- Impressions on `tribute band`-family queries in case the dual framing opens a new query cluster.

Success = meaningful CTR lift on any of the five primary queries within 4 weeks. Failure modes worth noting: if impressions drop sharply, the title change may have de-matched some ranking queries — iterate. If impressions stay flat but CTR doesn't move, the snippet change wasn't strong enough — consider a more aggressive meta description.

**Original problem statement** (preserved for historical context):

GSC audit 2026-04-19 revealed `/lander` is ranking (weakly, avg position 32.8) for high-intent commercial queries but converting almost none of them: 109 impressions, 1 click, CTR 0.9% over last 28 days. Ranks for the exact queries we want to win:

- `dallas cover bands` (17 imps, pos 40) — top commercial-intent phrase in the data
- `cover bands in dallas` (2 imps, pos 44)
- `dallas cover band` (2 imps, pos 48)
- `80s cover band dallas` (3 imps, pos 22)
- `80s tribute band near me` (1 imp, pos 11)
- `best cover bands in dallas` (2 imps, pos 76)
- `dallas tribute bands` (1 imp, pos 41)
- `dfw cover bands` (3 imps, pos 28)
- `iconic band dfw` (1 imp, pos 25)
- `live bands for events in dfw` (8 imps, pos 67)
- `risky business` (2 imps, pos 8.5) — legacy-band name still attracting traffic

**Why this matters:** `/lander` was built as a Bandzoogle-merger announcement page, not as a conversion page. It appears to be Google's current best guess for commercial queries because the legacy domains redirect to it. The root domain `/` ranks at position 3.3 but for far fewer queries. Once R4 ships and `/home` 301 consolidates, `/lander` may become an even more prominent landing spot — its current conversion UX will start mattering more.

**Plan:**
1. Pull the actual `<title>`, meta description, H1, and above-the-fold copy from `/lander` and compare against the queries above. Likely gap: page reads "we merged two bands" to visitors who searched "dallas cover bands."
2. Decide whether `/lander`'s job should stay "explain the merger" or become "capture merger-era traffic AND convert cover-band seekers."
3. If the latter: add a primary CTA (consistent with `-marketing` Section 11 one-primary-CTA guideline), tighten title/meta for the top query clusters, ensure band-identity signals (genre, location, booking path) are above the fold.
4. Decide separately whether `/lander` should be the `dallas cover bands` landing page at all, or whether R18 (locale SEO pages) should supersede it over time.

**Depends on:** Nothing urgent. Can ship standalone. Best done before R18 so R18 can link back to a page that converts.

**Priority:** Medium. High-leverage for a small edit — these are the exact intent queries the band exists to capture, and we're already ranking for them weakly.

---

### R20. Radio-station page intent-mismatch review

GSC audit 2026-04-19 surfaced two "station" pages pulling heavy impression volume on queries that don't match the band-booking business model:

- **`/the-all-oldies-hits-station`** — 200 impressions, 0 clicks, avg position 10.4
- **`/the-classic-rock-station`** — 115 impressions, 1 click, avg position 37.2
- **`/the-all-80s-hits-station`** — 28 impressions, 0 clicks, avg position 16.4
- **`/the-all-70s-no-disco-hits-station`** — 9 impressions, 0 clicks, avg position 6.7

Ranking queries on `/the-classic-rock-station` tell the story:

- `classic rock radio station`, `classic rock station`, `classic rock station fm`, `fm classic rock stations`, `local classic rock station`, `rock radio station`, `radio rock station`, `rock station`, `radio station rock music`, `the rock radio station`…

These searchers want an **FM radio station to listen to** — not a cover band to hire. The impressions are effectively hallucination traffic: Google matched our page title keywords, but the searcher intent is incompatible with booking a live band. 200 impressions with 0 clicks on `/the-all-oldies-hits-station` confirms the snippet never converts.

**Options:**

1. **Keep as-is** (status quo). They cost nothing; the branding exposure is free, just non-converting. Accept that these pages exist as part of the brand story ("we play hits from these eras") even if their SEO behavior is off-target.
2. **Retitle for booking intent** — rewrite `<title>` and H1 to lead with band-booking language ("80s Hits — Book Our 80s Set for Your Event"), keeping the setlist showcase underneath. Tries to convert the leaked traffic into booking interest.
3. **Noindex or remove** — tell Google to stop ranking these for radio queries. Clean, but loses all brand impressions.
4. **Repurpose as setlist-by-era pages** — merge with the setlist theme analysis work in `-marketing` (see R7). "80s Hits Setlist" as a genuine booking asset, not a station pretender.

Ray's call which direction this goes — the framing matters a lot for band identity.

**Depends on:** R7 context (setlist theme analysis) if option 4 is chosen.

**Priority:** Low-to-medium. Not a bug, not urgent. Revisit when there's appetite for a content pass.

---

### R21. Verify /home 301 consolidation after Google re-crawl

R3 (closed 2026-04-19) deployed a Cloudflare Page Rule `*liveradiodfw.com/home*` → 301 → `https://www.liveradiodfw.com/`. GSC audit 2026-04-19 surfaced a finding that makes this rule higher-stakes than the R3 close-out assumed: **`/home` was carrying 61% of site clicks** (17 of 28 clicks over the last 28 days) and 143 of 644 impressions, at avg position 14.4.

Implication: once Google re-crawls and honors the 301, `/` (root) inherits `/home`'s link-equity and impression volume. Best case: `/` (currently avg position 3.3 on lower volume) rises further and consolidates all the signal. Worst case (less likely but real): transient ranking dip during re-crawl flux, 1-3 week dip in clicks before recovery.

**Plan:**
1. At 2026-05-03 R4 reassessment, pull GSC performance by-page for the last 14 days. Confirm `/home` impressions trending to zero (Google has seen the 301), and `/` impressions rising to roughly the sum of the old `/home` + `/` volumes.
2. If `/home` impressions have not dropped by 2026-05-03, investigate: either the 301 is not firing for Googlebot specifically (rare), or Google has not re-crawled yet (likely — re-crawl cadence for a low-authority site can be slow).
3. If clicks to `/` are significantly below the prior `/home` + `/` sum and it's past 2026-06-01, deeper investigation (canonical tag conflicts, internal link audit).

**Monitoring safety net already in place:** UptimeRobot (R2) catches outages; monthly availability email clicks (`-marketing`) are independent of Google; Mailchimp venue-contact list is independent of Google. So even a worst-case search-traffic dip would not touch the primary booking-pipeline.

**Depends on:** Time — Google re-crawl cadence. Earliest meaningful check: 2026-05-03.

**Priority:** Medium — fact-finding only, no work to do until 5/3.

---

### R18. Locale SEO landing pages ("band-type in location" search capture)
Dedicated SEO landing pages targeting "{band-type} in {city}" intent queries — e.g. `cover band in Frisco`, `80s cover band Plano`, `live band Grapevine TX`, `wedding band The Colony`. We earn the right to rank for these because **we've actually played in those cities**: the R16 historic import + ongoing calendar give us genuine proof-of-presence, which is exactly the kind of local signal Google rewards and which thin "directory" competitors can't match.

**Why this works (the angle Ray surfaced):**
- Intent-rich: someone searching "cover band in Plano" is closer to booking than someone searching "cover band DFW"
- Content we already own: every show in that city is a real event at a real venue with a real date — not keyword-stuffed filler
- Local relevance signals: venue names, street addresses, city + TX in body copy, outbound-style references to the venues themselves
- Scales naturally with R16 follow-ups: every placeholder description Ray enriches makes the city page it appears on richer too

**Candidate cities (public-show counts after R16 import, verified against shows.json 2026-04-18):**
Frisco (19), Allen (19), Fate (16), Grapevine (9), Carrollton (5), The Colony (4), Royse City (4), Plano (3), Addison (3), Lewisville (3), Bonham (2), Denton (1), Terrell (1), Rockwall (1), Flower Mound (1), Dallas (1), Prosper (1), Sunset (1), Sanger (1).

Cut line: cities with ≥3 shows get a page in the first batch — **10 pages**: Frisco, Allen, Fate, Grapevine, Carrollton, The Colony, Royse City, Plano, Addison, Lewisville. The rest wait until they hit the threshold via natural booking cadence.

**Page shape (one per city):**
- URL: `/cover-band-{city-slug}` (extensionless, matches site-wide canonical convention established 2026-04-21 B25). Actual file lives at `cover-band-{city-slug}.html` in the repo; GitHub Pages serves it extensionless.
- `<title>` and `<h1>` targeting the intent query: e.g. *"Cover Band in Frisco, TX | Live Radio DFW"*
- Meta description built from real stats: *"Live Radio DFW has played 14 shows in Frisco at venues like The Frisco Bar & Grill and Frisco Rail Yard. Book us for your Frisco event."*
- Intro paragraph with city + venues naturally worked in (no keyword stuffing)
- Show list for that city (past + upcoming), using R17 calendar icons, each linking to its individual show page
- Venue highlight strip: a line per distinct venue played in that city ("Played 6 times at The Frisco Bar & Grill on Gaylord Pkwy")
- "Book us in {City}" CTA linking to `/book` with city pre-filled if possible
- Internal links: to `/songs`, `/videos`, nearby-city locale pages (adds link equity across the set)
- Schema.org `MusicGroup` + `Place` + `Event` structured data so Google can render rich results

**Technical plan:**
- New builder `build_locale_pages.py` in `lrdfw-ghpages/`. Groups `shows.json` by `address_short`, renders one HTML per qualifying city from a shared template.
- Intro/pitch copy is hand-curated per city the first time (stored in a new `_data/locale_copy.json` or inline in the builder) so each page reads like a real page, not a generated one. Machine assembles the data grid; humans own the voice.
- Builder runs in the same pipeline as `build_shows.py` and `build_show_pages.py`.
- `update_sitemap.py` extended to include locale pages.
- Footer link — "Where we play" hub page that lists all locale pages.

**Depends on:**
- R16 historic import (done) — supplies the show density per city
- R17 calendar icons (open) — ideally ships first so locale-page show lists use the upgraded visuals
- R13 style-guide audit (open) — should weigh in on URL convention and intro-copy voice before we cut 9 pages at once

**Priority:** Medium-high. Long-tail SEO play with authentic content, and the content substrate already exists post-R16. Compounds with every future show and every R16 description enrichment.

---

### R22. Station / Theme / Show taxonomy + build-out of named ready-to-book shows

Two related problems surfaced at the end of R19 smell-testing:

**Problem 1 — Taxonomy.** The site currently calls the four genre buckets "Stations" (The All 80s Hits Station, The Classic Rock Station, etc.). Internally we also talk about "themed shows" (A Tribute To MTV, Graduation Night, Texas Music Night) as a separate product category. On `/lander` we shipped both concepts back-to-back without resolving what to call each one. Open question: is "Station" the right public-facing word, or is "Theme" / "Show" / something else closer to what a venue talent buyer or party planner would (a) search for, and (b) understand when they see it in nav or a section header? Ray's hunch is we need more specific stations plus a clearer word — this item is for working through the naming and the information architecture together, not just renaming in place.

**Problem 2 — We have named ready-to-book shows with no pages.** `/lander` now names A Tribute To MTV, Graduation Night, and Texas Music Night as ready-to-book themed products. Ray has built several others over time that "even I have already forgotten" — they are floating around the marketing repo, old drafts, or memory. With relatively little work each becomes a page: pick the songs from the existing catalog, write a short pitch, ship. But we don't have a runbook for adding one, and we don't have an inventory of which shows exist.

**Architecture discovery (2026-04-19 while filing this item):**
- `gh-pages/stations.json` exists with 4 entries (80s, 70s no-disco, classic rock, oldies) carrying id / name / slug / short+long description / BandHelper smart-list widget IDs.
- **No file on `gh-pages` references `stations.json`** (verified via `grep -rn "stations.json"` across HTML / JS / Python). The four station HTML pages are fully hand-built — song lists embedded directly in HTML, BandHelper widget IDs also hard-coded per page. So `stations.json` is currently orphaned data. Either (a) a prior attempt at data-driven station pages that never shipped, (b) intended for a future build step, or (c) stale. Needs a call: delete it, wire it up, or leave it and document why.
- Nav structure: station links live under the Songs dropdown only. No top-level "Themes" or "Shows" dropdown. If we add themed-show pages, IA changes.

**Plan:**
1. **Inventory the floating shows.** Search `liveradiodfw-marketing` repo (setlist theme analysis, old campaign drafts, style guide) and Ray's memory for every named ready-to-book show concept. Produce a single list with: name, one-line pitch, rough era/audience, whether setlist is ready or needs curating. Start with MTV, Graduation Night, Texas Music Night and grow from there.
2. **Resolve taxonomy.** Decide on public-facing words for the two (or more) concepts. Candidates: Station (genre bucket) vs. Themed Show / Tribute Show / Show (named product) vs. collapse into one category vs. something else. Evaluate against: search intent (what does a party planner type?), scan-ability (what does a venue buyer understand in the nav in under two seconds?), honesty (we are a cover band doing era-and-audience tributes, not artist tributes), and room to grow (the named-show list will expand). Low-cost external input: run 3-5 candidate terms past GSC Keyword Planner / Google Trends for the DFW region.
3. **Decide `stations.json`'s fate.** If we go data-driven for themed shows, extend the schema and wire the station HTML files to it too (kill the duplication). If not, delete `stations.json` to stop the next person thinking it's load-bearing.
4. **Write the "add a new themed-show page" runbook** in `docs/runbooks/` — templated file, nav-update checklist, sitemap.xml entry, GSC index submission, internal link from `/lander` Custom Tribute Shows paragraph, `stations.json` update (if we keep it). Do this before building the first page so the process is codified.
5. **Build pages for the named shows, in priority order** decided with Ray. Each page lands with: H1 + meta tuned to search intent, setlist table, short pitch, hero image (or placeholder), CTA. Link from `/lander` Custom Tribute Shows paragraph so the named shows become clickable rather than just text.
6. **Add more specific stations** per Ray's note — candidates emerge from the marketing-repo setlist theme analysis. Same runbook applies.

**Depends on:**
- R13 style-guide audit — ideally weighs in on voice and naming conventions before we build pages at scale.
- R11 head-level includes — if that ships first, nav changes for the new taxonomy are a single-file edit instead of a 15-file sweep. Strongly recommend R11 ships before step 5.

**Priority:** High. Ray called it out explicitly in the R19 smell-test as a high-priority roadmap item, and it compounds the R19 `/lander` investment — every named show we build becomes a landing page for its own search intent ("MTV tribute band dallas", "graduation party band dfw", "texas music cover band") and a conversion target the `/lander` CTA can eventually route to. Belt-and-suspenders concern: the floating-shows list is currently in Ray's head only, and heads forget. Getting it written down has value on its own, even before any page is built.

---

## Marketing automation

### R6. Merger intro campaign
Drafts exist in the `liveradiodfw-marketing` repo. Decide on timing and target audience (existing Jackson Crossing / Risky Business contacts, current Venues list, new-prospect list).

### R7. Setlist / theme analysis rollout
Analysis assets already live in `liveradiodfw-marketing`. Decide whether/how to expose on the public site (e.g., per-Station landing pages beyond the homepage Stations overview).

### R12. End-to-end booking links in the monthly availability email

Today the monthly availability email (generated by `liveradiodfw-marketing/liveradiodfw_availability.py` + Mailchimp template, Tuesday 9am Central, last-Tuesday-of-month) lists the band's open dates as plain text and asks the recipient to "reply" to book. Turn each open date into a "Book {date}" link that drops the venue contact into a pre-populated booking form on `liveradiodfw.com`, so a venue can commit without an email thread. Booking-manager adoption is unknown, but the friction delta (reply vs. one click) is real and low-cost to test.

**Plan:**
- New public page (e.g., `/book?date=YYYY-MM-DD&mc_id={MC_MERGE_TAG}`) with a form that already knows: the date being booked, the venue name, the contact's name, the contact's email, and — if Mailchimp has them as merge tags on the Venues list — prior-booking flag, house sound/lights policy, typical pay, load-in notes, stage size, PA details.
- Mailchimp template change: wrap each list item in an anchor with the date + Mailchimp merge tags in the query string so the landing page renders pre-filled.
- Form submit path: post to the existing Apps Script webhook (same endpoint that handles GCal writes) with a new action (e.g., `action="booking_request"`) that creates a tentative GCal event on `info@liveradiodfw.com` with the venue as attendee and emails Ray + the venue a confirmation. Or, simpler first pass: form submit just emails a structured booking request to Ray and logs to a Sheet; tentative GCal write comes later.
- Two-click-confirm pattern for Ray so a venue click doesn't auto-book without his ack.

**Design questions to settle before build:**
- Which Venues-list merge tags already exist in Mailchimp vs. need to be added? (sound/lights, pay, load-in, prior-booking).
- Does the form need to collect anything beyond what Mailchimp already knows? (set time, headcount expectation, specific ask).
- Tentative-event creation in GCal now vs. email-first now and GCal later.
- Analytics: we need click-through and form-submit tracking from day one to answer "do booking managers actually use this," otherwise the feature runs on faith the same way the current email does.

**Depends on:** B1 (DST cron alignment) should be settled first, since any link scheme ties to the exact send cadence. Mailchimp Venues-list merge-tag audit.

**Priority:** Medium. Cool factor is high, adoption is unknown, and the supporting data (merge tags, analytics) is a prerequisite. Ship after foundation items (R11, B12, B7 Part 2).

### R13. Style guide vs. site copy audit

The authoritative brand voice lives in `liveradiodfw-marketing/MARKETING_STYLE_GUIDE.md`, but site copy across `liveradiodfw-site` (home hero, Stations pages, about, press-kit body, booking page intro, error strings, footer taglines) was written piecemeal across many sessions without ever being checked against the guide. Likely drift in voice, terminology, and tone. One-time audit to catch drift, plus a checklist so future copy edits diff against the guide before landing.

**Plan:**
- Jarvis reads the style guide and extracts the hard rules (terminology, capitalization, forbidden words, voice descriptors, tagline variants).
- Jarvis diffs every user-facing string in `-site` against those rules and produces a findings doc in `docs/` with proposed edits, grouped by severity.
- Ray reviews, says yes/no per item, Jarvis lands the approved edits.
- Add a line to the end-of-session runbook: "if user-facing copy changed, diff it against the style guide."

**Depends on:** Nothing. Jarvis can run the audit solo and surface findings for review.

**Priority:** Low. No user-visible bug, but the drift compounds every session. Worth one clean pass.

### R23. Preserve and document the Monthly Profile Audit venue-discovery cron

**Context:** The Monthly Profile Audit is the first band-marketing project Ray ever ran with Jarvis. It searches the DFW metroplex for new live-music venues and adds any net-new finds into the Mailchimp **Venues audience** (`97cca06eff`) so the monthly availability email reaches them. It is currently live as a Perplexity `schedule_cron` task named "LiveRadioDFW Monthly Profile Audit" (next fire ~2026-05-01), owned by the Perplexity thread "More Band Marketing" — invisible from every other thread per [bugs.md J1](bugs.md#j1-scheduled-tasks-are-invisible-across-threads). The script logic lives only inside that thread's message history. None of it is committed anywhere. If that thread is lost, restarted, or garbage-collected, the job and its source both vanish. Mailchimp activity confirms it is working — 15 `other_adds` hit the Venues audience on 2026-03-30 (one-day spike consistent with a monthly batch), and a trickle of 1-3 hand-processed adds afterward.

**Why now:** Two compounding loss vectors. (1) J1 — the cron is thread-scoped and Ray starts a fresh thread most days because Perplexity drifts within a long session; Ray cannot see or edit this task from any new thread. (2) The script itself was never extracted from conversation history, so even if the cron is found it can silently stop working with no recoverable source. The job fires again around 2026-05-01, which is the natural moment to verify it ran, pull the logic out, and migrate it somewhere durable.

**Plan:**
- **Forensics:** Open the Perplexity "More Band Marketing" thread, locate the scheduled task's `task` prompt (that is the full spec that runs each month), and copy it verbatim into `liveradiodfw-marketing/venue_discovery/` (new folder). Also pull any prior-run outputs still visible in the thread — the sources it searches, the filtering heuristics, the "is this a live-music venue" decision logic, whatever dedupe strategy it uses against the existing Venues audience.
- **Mailchimp audit:** Pull the last 12 months of `other_adds` on Venues audience `97cca06eff` and any tags/merge-fields the job writes. Document the contact shape the job produces (email, venue name, city, tags, any merge fields) in `architecture/marketing-automation.md` so future edits don't break the shape the availability email expects.
- **Extract and rewrite as a committed script:** Produce `liveradiodfw-marketing/venue_discovery/discover_venues.py` that codifies the logic. Secrets (Mailchimp API key, any search API keys) read from `.env` or OS env, not hard-coded — same pattern we're establishing for B7 Part 2's `sync_runner.py`.
- **Migrate to the Windows box alongside `sync_runner.py`:** Once B7 Part 2 lands, the Windows Task Scheduler is the durable host for all band crons. Add a Monthly Profile Audit task there (last-Sunday-of-month or similar; settle cadence when we see the real cron's firing pattern). Delete the Perplexity `schedule_cron` task in the same move so we don't double-fire.
- **Document in `architecture/scheduled-tasks.md`:** Add a third row (alongside Daily calendar sync and Monthly availability email) the same day the Perplexity cron is replicated, BEFORE deleting the Perplexity version. Cardinal rule per that file's "Rules for adding new scheduled tasks."
- **Close loop:** Link this R23 entry from J1 as an instance of the blind spot, and from the new Windows Task Scheduler runbook (B7 Part 2 deliverable) as the second job that box now owns.

**Depends on:** Nothing blocks forensics or the Mailchimp audit. Migration depends on B7 Part 2 landing the Windows Task Scheduler + `.env` pattern (the Monthly Profile Audit is the second customer for that infrastructure, not the first).

**Priority:** High. The job fires again around 2026-05-01 — that is the last easy checkpoint before another month of drift. First band-marketing project Ray built with Jarvis; losing the source would be a real regression.

---

### R24. Windows Task Scheduler "run whether user is logged on or not" for daily calendar sync

**Context:** B7 Part 2 install on 2026-04-21 PM registered `LiveRadioDFW Daily Calendar Sync` on Windows Task Scheduler via `setup_sync_task_scheduler.ps1`. The task is in `Ready` state and will run daily at 8:00 AM Central. **However**, the task is currently configured as **"Run only when user is logged on"**, which means if Ray reboots the machine overnight and doesn't sign back in before 8 AM, the sync silently skips that day.

**Why it's in this state:** Switching to "Run whether user is logged on or not" requires typing Ray's local Windows account password into a credential prompt. Ray uses **Windows Hello (PIN / biometrics)** for daily unlock and does not have the underlying account password memorized or saved anywhere. Resetting the password via `netplwiz` would work but carries a small DPAPI side-effect footprint (some Edge-saved credentials, some Wi-Fi profiles may need re-entry). We punted on the password reset rather than take that risk for what is currently a theoretical failure mode.

**Why it's probably fine for now:** Ray is active on this machine daily. Screen-lock does NOT count as logged-off — his session persists. The only scenario that breaks the sync is a reboot followed by nobody signing back in before 8 AM. The 3-day parallel run against the old Perplexity cron (post-B7 close-out) will expose any skipped days immediately: if the Perplexity sync pushes a diff the Windows sync missed, we know the "logged on" mode bit us. Until that happens, the risk is purely hypothetical.

**The fix path, when we commit to it:**
1. Reset the local Windows password for account `myers` via `netplwiz` (Windows key + R → `netplwiz` → select user → Reset Password). Choose something long, save in 1Password as `Windows login - myers`.
2. Re-authenticate Hello (it should continue working unchanged, but confirm).
3. Task Scheduler → right-click `LiveRadioDFW Daily Calendar Sync` → Properties → General tab.
4. Select "Run whether user is logged on or not" (leave "Do not store password" UNCHECKED — we need network access for git push).
5. Enter the new password at the credential prompt.
6. Verify: right-click task → Run → confirm it executes successfully from stdout/sync.log. Then reboot, **don't sign in**, wait past 8 AM, confirm the sync ran anyway.
7. Add the new password to the runbook's "Required credentials" section (pointer to 1Password entry; never the password itself).
8. Note in the runbook that any future Windows password change will break the task and requires re-entering the new password in Properties.

**Fallback if we never want to touch the password:** Accept "logged on" mode as the contract. Add a note to `runbooks/windows-sync-task.md` that any day that starts with a rebooted-and-not-signed-in machine will skip the sync, and that the remedy is to sign in and run the task manually (right-click → Run). Acceptable for a personal dev box that Ray lives on every day.

**Dependencies:** B21 forensics completion doesn't block this, but *does* provide useful context — one of the six orphaned Perplexity tasks (the one running hourly) may reveal patterns about how often a truly-daily cadence matters vs. a more flexible window.

**Priority:** Low. File-and-forget until the parallel run surfaces a missed day. Re-open with urgency only if the "logged on" mode produces a real production gap.

**Status:** Open. Filed 2026-04-21 PM during B7 install close-out.

---

### R25. Reply-to-approve workflow for show descriptions

**Context:** The daily calendar sync flags new public shows that are missing their About-this-show description and emails Ray a machine-generated draft under "Proposed description draft" (sync_runner.py, via sync_lib.generate_description_draft). Until today the only way to move a draft into `shows.json[show].description` was for Ray to open a Jarvis session, paste the draft in, re-run it through tone calibration, and ship the final hand-curated copy. Most of the time the machine draft is already close enough that the ceremony of a full session is overkill; for the copy that does need enrichment, the friction of round-tripping through a session is also the bottleneck. The approval step is valuable (cardinal rule: Ray approves before publish), but the approval step is ceremony, not engineering.

**Why now:** 3 Nations Brewing 2026-09-05 is the concrete instance that surfaced the gap on 2026-04-23 AM session. New public shows land via the 8 AM sync at roughly one-per-week cadence as bookings close. Every one of those triggers a "proposed draft in email that nothing can act on" event. Compounding: the previously-assumed Stage 2 rollout for auto-generated descriptions (B16.2, P3) needs approval data points before it can progress, and we currently have zero because there is no low-friction way to record an approval decision.

**Constraints:**
- Ray is the only person with access to `info@liveradiodfw.com` today; trust boundary is low-risk.
- Approval must remain a human-in-the-loop step. No auto-publish under any circumstance.
- Must work identically from iPhone (Outlook mobile) and desktop (Outlook browser), which is where Ray reads `info@`.
- Cannot depend on Perplexity thread scheduling (J1 / B21 orphan-cron pain).
- Must enforce cardinal rules (ASCII only, no em-dashes, no smart quotes) before anything lands in `shows.json`.
- Does not require a new mailbox or DNS change.

**Plan (3 parts):**

- **Part A - Upgraded alert email (SHIPPED 2026-04-23 AM).** `sync_lib.build_approval_email_section()` renders the MISSING-INFO block for a description-missing show with APPROVE and EDIT mailto links that include a stable 12-char sha256 token in the subject line. `sync_runner.py` calls the new helper when a draft is available. Tests for token stability, cross-show invariance, ASCII gate, and em-dash gate added to `test_description_handling.py`. Scaffold `approvals/pending.json` committed with the schema Part B will write. Shipped as first commit of 2026-04-23 AM session on master in liveradiodfw-site and master in liveradiodfw-marketing.
- **Part B - `process_approvals.py` on the Windows box (next session, est. 2 hours).** New script on Ray's box at `C:\Tools\LiveRadioDFW\` alongside sync_runner.py. Runs every 15 minutes via a second Windows Task Scheduler task. Polls `info@liveradiodfw.com` over IMAP, matches reply subjects against `pending.json` tokens, and on match: writes `shows.json[show].description`, commits as "Ray" to master, pushes, removes token from pending, appends to `approvals/log.json`. APPROVE writes the draft verbatim. EDIT parses everything after `TOKEN: <token>` in the reply body as the final description. Sender allowlist: `info@liveradiodfw.com` and `rmyers@futurebright.com` initially; extensible to delegates (Donna) later. Cardinal-rule gates (ASCII, em-dash, smart quote) enforced pre-commit; any violation rejects the reply and sends a short failure email back so Ray can resubmit.
- **Part C - Stage 2 auto-publish data collection (deferred, B16.2 territory).** Once Part B is exercised 5+ times and trust is established, collect quality data on how often Ray approves vs. edits. If approval rate is high enough, a `--auto-approve` mode for routine venue refreshes (repeat bookings at already-described venues) becomes the natural next step. Pairs with B16.2.

**Token design:** `sha256(date|venue|draft)[:12]`, placed in the mailto subject as `APPROVE <token>` or `EDIT <token>`. Subject-based matching (not plus-subaddressing) so the flow does not depend on mail-host configuration and works identically for any future delegate.

**Depends on:**
- Part A: none (shipped).
- Part B: B22 Gmail SMTP pattern (shipped) provides the email credential template; Part B reads over IMAP using the same app password pattern. Windows Task Scheduler second-task install follows the B7 Part 2 pattern documented in `runbooks/windows-sync-task.md`.
- Part C: 5+ real approval data points through Part B; B16.2 coupling.

**Priority:** High for Part B (removes manual friction from every new-show flow; 3 Nations Brewing is the first instance). Medium-Low for Part C (nice-to-have, not on a deadline).

**Status:** Part A shipped 2026-04-23 AM. Part B queued for next session. Part C deferred.

---

### R26. Cloudflare cache purge tool

**Context:** The site is served through Cloudflare (Free plan) with an edge TTL of ~10 minutes. After a git push to master the live site can lag behind origin by up to that long. For Ray's own verification `audit_shows.py` appends `?v=<timestamp>` which forces a fresh fetch but does NOT invalidate the edge cache that everyone else sees. Three concrete cases where that matters:

- A venue contact is about to click a link we just sent and we need the edge to reflect origin *now*, not in 10 minutes.
- Social preview fetchers (Facebook debugger, Mailchimp preview, iMessage unfurl) don't respect query strings; they see the stale copy.
- A content bug is live and we want it off the edge within seconds, not on the TTL clock.

Ray created a minimum-scope Cloudflare API token on 2026-04-21 with `Zone > Cache Purge + DNS` permissions on the `liveradiodfw.com` zone. The token existed but there was no tool in the repo that used it; a prior Perplexity thread did ad-hoc `purge-files-by-url` API calls but nothing was ever committed. Gap identified and closed on 2026-04-23 AM session.

**Shipped 2026-04-23 AM:** `purge_cache.py` in `liveradiodfw-site` repo root. Stdlib-only, ASCII-only, ~240 lines.

Modes:
- `python purge_cache.py https://www.liveradiodfw.com/shows.json` - specific URLs (up to 30, Cloudflare Free plan limit)
- `python purge_cache.py --shows` - the common bundle: `/shows.json`, `/`, `/shows` (after a calendar-driven content change)
- `python purge_cache.py --everything` - whole-zone purge (slower edge rebuild, use sparingly)
- `--dry-run` prints what would be purged without calling the API (safe to run without a token)
- `--no-verify` skips the post-purge `cf-cache-status` HEAD check

Reads `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ZONE_ID` from `.env` at the repo root (same loader pattern as `GIT_BRANCH` today) with env-variable override. Exit codes: 0 success, 1 config error, 2 API call failed, 3 post-purge verification failed.

Post-purge verification is built in: the script HEADs each purged URL with a cache-buster and reports `cf-cache-status`; `MISS`, `DYNAMIC`, `EXPIRED`, or `BYPASS` all mean the edge just pulled from origin, which is what we want. A `HIT` immediately after a purge would mean the purge silently failed, and exit code 3 makes that loud.

Tests: `test_purge_cache.py`, 25 cases, all passing. Covers ASCII gate, argument parsing (no args, >30 URLs, dry-run shapes), env-file loader (plain KEY=VALUE, quote stripping, no-override, missing file, bad lines), and monkey-patched `api_purge` for both success and failure paths. No network calls in the test suite.

**Wiring pending (next session, ~15 min):** Add `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ZONE_ID` to Ray's `.env` on the Windows box at `C:\Tools\LiveRadioDFW\liveradiodfw-site\.env`. Smoke-test `python purge_cache.py --dry-run --shows` first to confirm the zone id loads, then `python purge_cache.py --shows` against live to confirm the API call works end-to-end.

**Future enhancement (not urgent):** Hook `purge_cache.py --shows` into `sync_runner.py` so the 8 AM daily calendar sync auto-purges the shows bundle after a successful push, but only when `shows.json` actually changed. Making this automatic removes the 10-minute visibility lag on every new booking. Defer until the tool has been used manually enough to trust it.

**Status:** Tool + tests shipped 2026-04-23 AM. Pending `.env` config on Windows box before first live use.

---

### R14. Enrich press-kit and booking pages with marketing-repo content ~~[OPEN]~~ → **PRESS-KIT OPENING SHIPPED 2026-04-19 (remainder open)**

**Partial ship 2026-04-19 (commits [`42965d4`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/42965d4), [`e850c1a`](https://github.com/TicoRicoRay/liveradiodfw-site/commit/e850c1a)):** Press-kit opening paragraph rewritten to match `/lander` positioning (ready-to-book themed shows named inline, tributes-to-eras-not-artists framing, drops the "Station shows tailored to any event" internal-memo phrasing from the prior draft). New "For venues and planners" proof block added below the bio with seven facts-only bullets: **together since 2021** (leading; Ray flagged this as a deliberate differentiator given how flaky many bands are), five-piece/five-vocalists, 100+ songs/six decades, ready-to-book themed shows, in-ear monitors, fully insured, DFW-based. "Start here" pin added to the Band Overview video. First draft of the opening paragraph said "formed from the merger" without a year, which was accurate-but-weak; Ray corrected mid-session with the important nuance that the musicians have been together since 2021, even though the Live Radio DFW name itself is post-merger. Final bio leads with "Same musicians playing together since 2021, now under one name after merging Risky Business DFW and Jackson Crossing" — honest about the rename, credits the five-year history. Lesson logged: when the band has a rename-but-continuity story, lead with the continuity; the rename is the footnote. What is explicitly NOT done in this pass and still open: recent-venues strip (depends on R5 or hand-curation), set-length options grid (needs Ray's input on which lengths are real), starts-at price figure (needs Ray), standalone "Why book us" page or `book.html` section addition, R13 style-guide alignment pass. Remainder of R14 stays open for those items.

**Positioning language shipped on `/lander` 2026-04-19 (R19) was the press-kit starting point — now deployed.** First draft used internal-memo framing ("versatility is what we offer, marketable theming is what the nicer venues want, we bridge the two") and Ray rightly flagged that those words were tuned for an internal conversation between us, not for the page's actual readers. Final shipped copy demonstrates the positioning through the product menu instead of announcing it:

> Some events call for more than a standard cover-band set. When you want a show with a theme — something you can promote, something with a hook — we bring a ready-to-book menu: A Tribute To MTV, Graduation Night, Texas Music Night, and more. Each one is a complete setlist plus the marketing package to promote it: a named show, a story, and the songs that deliver it. Built around an era, an audience, or a cultural moment rather than a single artist. Have a theme of your own? We'll build the setlist around it.

**Key craft decisions that should carry to press-kit work:**
- "Show with a theme — something you can promote, something with a hook" is the reader-facing translation of "marketable theming." Venue buyers recognize that as their actual pain.
- "Complete setlist plus the marketing package to promote it: a named show, a story, and the songs that deliver it" surfaces the real differentiator (ready-made promotional assets per show) in concrete terms a talent buyer scans in one pass.
- Avoid internal-memo phrasing on public pages. Any time we find ourselves writing "we bridge X and Y" or "versatility is what we offer," that's a sign we're narrating our own strategy rather than selling a product.
- The tribute-to-era-not-a-single-artist framing is the honest-and-useful way to claim tribute-show capability without overclaiming — reuse verbatim on press-kit.

When press-kit work starts, this copy (not the first-draft internal-memo version) is the starting point for the opening paragraph of the venue-facing pitch — don't rewrite from scratch.


`press-kit.html` exists as an EPK (bio, photos, stage plot) but does not surface the setlist theme analysis, merger narrative, or talent-buyer-oriented proof points (crowds drawn, venues played, price range, logistics). `book.html` is purely an inquiry form, not a sales page; there is no page aimed at a venue talent buyer asking "why should we book you over another band." The content to answer those questions now lives in `liveradiodfw-marketing` (setlist theme analysis, intro campaign drafts, style guide positioning).

**Plan:**
- **Press kit additions:** short "recent venues" strip (pulled from GCal history once R5 lands, hand-curated until then), press-style one-paragraph pitch sourced from the style guide, one-line set-length options (45/60/75/90/120 min), link to Videos page with a specific "if you only watch one" pin.
- **New "Why book us" page** (or a section added to `book.html` above the form): talent-buyer framing. Crowd we draw, markets we play, typical set structure, PA / monitoring self-sufficiency (in-ears noted), insurance, load-in realities, price range (even a "starts at" figure reduces dead-end inquiries). Setlist theme analysis gives us the raw material for "here's the catalog depth" claims that are specific, not fluffy.
- Keep the talent-buyer page distinct from fan-facing pages (home, songs, videos). Different audience, different tone.

**Depends on:** R13 (style guide audit) ideally ships first so the new copy lands already aligned to the guide instead of needing a rewrite pass.

**Priority:** Medium-high. Directly addresses the top of the booking funnel (a venue scout's first visit), which is more leverage than any single optimization to the existing pages.

---

## Decisions pending (not bugs, but blocking other work)

### R8. Regina as event attendee - method decision ~~[PENDING]~~ → **DECIDED 2026-04-17 PM (option b)**
See [bugs.md B2](bugs.md#b2-webhook-attendees-field-is-a-silent-no-op). Ray chose option (b): extend the `_updateEvent` webhook so automation can add attendees. R10 implemented the code change and it's deployed. The optional post-sync step in `sync_calendar.py` to auto-add Regina to every future public event is not yet implemented — if we want that, file a new R-entry for it rather than reopening R8.

### R9. Timezone convention enforcement — **STANDING RULE, ENFORCED AT END-OF-SESSION 2026-04-19**
Standing rule: all user-facing language uses "Central" or "America/Chicago", never "CDT" or "CST". Swept once on 2026-04-17.

**Closed 2026-04-19:** reframed from a "planned work" item (which it never really was) into an active enforcement mechanism.

1. **End-of-session grep hook added** to [runbooks/end-of-session.md](runbooks/end-of-session.md) as new step 4 — before committing, diff-scope the session's files for `\b(CDT|CST)\b` and fix user-facing violations in the same commit. Legitimate exceptions (Python identifiers, rule-quoting text, linter code) are called out explicitly so the check doesn't produce false-positive fatigue.
2. **Existing violation filed as real bug.** A full-repo sweep on 2026-04-19 found two user-facing `"CDT"` strings in `sync_calendar.py:677` and `:731` (alert email bodies). Previously half-mentioned in B15's follow-ups section but never filed. Now tracked as [B17](bugs.md#b17-sync_calendarpy-alert-email-copy-uses-cdt-string-cardinal-rule-violation).
3. **Rationale for closing as a standing rule, not a one-time item.** Enforcement lives in two places now: `audit_shows.py` (catches HTML leaks at build time) + end-of-session runbook step 4 (catches prose/code leaks at commit time). No further roadmap tracking needed; new violations surface as bugs via the hook.

**Priority:** ~~(not scored)~~ N/A (closed).

### R10. Extend `_updateEvent` to honor attendees ~~[OPEN]~~ → **DONE 2026-04-17 PM**
Dependency for [B2](bugs.md#b2-webhook-attendees-field-is-a-silent-no-op). `_updateEvent` previously accepted the `attendees` payload field but had no code path that acted on it.

**Delivered 2026-04-17 PM:**
1. ✅ Extended `_updateEvent` in `docs/scripts/LiveRadioDFWCalendar.gs` to iterate `data.attendees || data.guests` and call `event.addGuest(email)` for each.
2. ✅ Normalized `_createEvent` to accept either field name as a bonus.
3. ✅ Both paths now return the resulting `guests:` array in the response for verification.
4. ✅ Published as Version 2 via [runbooks/publish-calendar-webhook.md](runbooks/publish-calendar-webhook.md) (same session the passphrase was rotated for B7 — coordinated change).
5. ✅ Smoke-tested against a throwaway event: `create` with `attendees: ["rmyers@futurebright.com"]` returned `guests: ["rmyers@futurebright.com"]`; `update` with a new attendee set returned the updated `guests` array; throwaway deleted.
6. ✅ B2 moved to Fixed Recently.
7. ⏭️ Optional `sync_calendar.py` auto-ensure-Regina step deferred — file a new R-entry if we decide to do it.

---

## Parked / someday-maybe

- Individual band-member bios on `/about` (names, instruments, roles) - currently the site says only "5 vocalists." Requires photos + copy.
- Social handles on the site - currently none published.
- Set-length and typical-show specs on the site for booking leads.
- Band finances tooling - explicitly outside this repo.
