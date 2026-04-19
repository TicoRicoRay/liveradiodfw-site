# DNS & GitHub Pages Runbook

_How liveradiodfw.com is served, who controls what, and what NOT to touch._

_Last verified: 2026-04-17_

## Current architecture

```
Visitor
   │
   ▼
Cloudflare (DNS authority + CDN + SSL edge)
   │  nameservers: summer.ns.cloudflare.com, titan.ns.cloudflare.com
   │  proxied (orange cloud on), Full SSL mode, Always Use HTTPS ON
   ▼
GitHub Pages (gh-pages branch of TicoRicoRay/liveradiodfw-site)
   │  CNAME file contents: www.liveradiodfw.com
   ▼
Static site
```

## Who controls what

| Service | Role |
|---|---|
| **GoDaddy** | Registrar only. Domain billing. Nameservers point to Cloudflare. |
| **Cloudflare (Free plan)** | DNS authority. CDN/proxy. SSL edge (Universal cert, Let's Encrypt under the hood). |
| **GitHub Pages** | Origin. Serves the static site from the `gh-pages` branch. |
| **GitHub** | Cert for `www.liveradiodfw.com` + apex (partially — see SSL section). |

**Do not edit DNS at GoDaddy.** All DNS records live in Cloudflare.

## Canonical URL

**`https://www.liveradiodfw.com`** is the canonical host.

- Apex (`liveradiodfw.com`) 301-redirects to `www` via Cloudflare.
- `CNAME` file on `gh-pages` branch contains exactly `www.liveradiodfw.com`.
- GitHub Pages custom domain is set to `www.liveradiodfw.com`.

## DNS records (current, in Cloudflare)

| Type | Name | Value | Proxied? | Purpose |
|---|---|---|---|---|
| NS | @ | summer.ns.cloudflare.com | — | Cloudflare nameserver |
| NS | @ | titan.ns.cloudflare.com | — | Cloudflare nameserver |
| A/CNAME | @ | (Cloudflare-managed) | ✅ | Apex → 301 to www |
| CNAME | www | (Cloudflare → GitHub Pages) | ✅ | Serves the site |
| CNAME | k2._domainkey | dkim2.mcsv.net | ❌ | Mailchimp DKIM |
| CNAME | k3._domainkey | dkim3.mcsv.net | ❌ | Mailchimp DKIM |
| TXT | @ | v=spf1 a mx include:sendgrid.net include:secureserver.net -all | — | SPF (SendGrid + GoDaddy mail) |
| TXT | @ | NETORGFT17335117.onmicrosoft.com | — | Microsoft 365 (Outlook) domain verification |
| TXT | @ | google-site-verification=UJCNN0r7stLcwEfTkoQElf94QyBT_Ep8Lk-nsPpc5Oc | — | Google Search Console |
| TXT | @ | google-site-verification=uMjN2KYIEzHniGxn4zgKZxfYGik4hKk3tmpYHBUdOm8 | — | Google Search Console (second property) |

### Open issue: missing GitHub domain-verification TXT

The `_github-pages-challenge-TicoRicoRay` TXT record that was documented in earlier checklists is **not currently present**. It may have been dropped during the Cloudflare migration.

GitHub uses this record to verify domain ownership for custom domains. Without it, you could theoretically lose the ability to reclaim the domain if it were ever taken over by another GitHub account — but Cloudflare proxying makes that effectively impossible right now.

**If GitHub ever asks for re-verification, pull the fresh challenge value from the repo's Pages settings and add it as a TXT record in Cloudflare.**

### SPF note

Current SPF includes `sendgrid.net` (whatever email-sending service is currently authorized) and `secureserver.net` (GoDaddy's mail). If you ever add transactional send from Mailchimp (not just campaign send), add `include:servers.mcsv.net` — but campaign-only Mailchimp does NOT require SPF changes because it sends `from:` its own domain.

## SSL

**Two certs are in play:**

1. **Cloudflare edge cert** (Universal, via Let's Encrypt) — what visitors actually see. This is the one that matters for uptime.
2. **GitHub Pages cert** — only used on the origin side (Cloudflare → GitHub). Currently in `dns_changed` state because of the Cloudflare proxy. **This is expected and fine** — Cloudflare is doing the public-facing TLS termination.

**`Enforce HTTPS` in GitHub Pages settings is OFF** — leaving it OFF is intentional while Cloudflare proxy is on and set to Full SSL mode. Cloudflare "Always Use HTTPS" handles the redirect at the edge.

### Verifying SSL health

```bash
# Visitor-facing cert (Cloudflare):
curl -vI https://www.liveradiodfw.com/ 2>&1 | grep -E "subject|issuer|expire"

# Apex redirect:
curl -sI https://liveradiodfw.com/ | head -3    # should 301 to www
```

## Repo & branch structure (standing rules)

| Repo | Branch | Role |
|------|--------|------|
| `liveradiodfw-site` | `gh-pages` | Live website |
| `liveradiodfw-site` | `docs` | Docs (this runbook lives here) |
| `liveradiodfw-marketing` | `master` | Monthly availability email automation + marketing assets. **Never serves any domain.** |

**Rule:** Site content lives in one place — `liveradiodfw-site` / `gh-pages`. Never duplicate across repos.

## Day-to-day site edits

1. Clone or pull `liveradiodfw-site`, checkout `gh-pages`
2. Edit, commit, push
3. Wait 30–60 seconds for Pages build
4. Verify at `https://www.liveradiodfw.com` (Cloudflare cache TTL is short — should appear within ~1 minute)
5. If stale, purge at Cloudflare → Caching → Configuration → Purge Everything, OR append `?t=<timestamp>` to bust

### Verify a Pages build finished

```bash
gh api repos/TicoRicoRay/liveradiodfw-site/pages/builds/latest --jq '{status, created_at, duration}'
```

Look for `status: "built"`.

## Things that WILL break the site

| Action | Risk | Prevention |
|--------|------|------------|
| Changing nameservers at GoDaddy | Immediate outage | Keep NS pointed at Cloudflare. Period. |
| Removing the `CNAME` file from `gh-pages` | GitHub Pages stops serving `www.liveradiodfw.com` | Don't delete it. Value must stay `www.liveradiodfw.com`. |
| Turning off the Cloudflare proxy (gray cloud) on `www` | SSL errors at the edge, possible origin exposure | Keep proxy ON. |
| Switching Cloudflare SSL mode away from "Full" | "Too many redirects" or SSL errors | Leave at **Full**. Never "Flexible". |
| Assigning this custom domain to any other GitHub repo | Immediate outage | Only `liveradiodfw-site` may hold `www.liveradiodfw.com`. |
| Force-pushing to `gh-pages` | Could wipe site history | Never force-push. |
| Hand-editing `shows.json` or `shows/*.html` | Overwritten on next daily sync at 8 AM Central | Edit the band Google Calendar instead — see [edit-ticket-prices.md](edit-ticket-prices.md). |

## Cloudflare Page Rules

Active Page Rules on the `liveradiodfw.com` zone. Free plan includes 3 rules; we currently use 1.

| # | Match pattern | Setting | Value | Purpose |
|---|---|---|---|---|
| 1 | `*liveradiodfw.com/home*` | Forwarding URL | 301 → `https://www.liveradiodfw.com/` | Legacy deindex cleanup. Catches any hit on `/home`, `/home.html`, `/home/`, `/home?...`, on apex or www, case-insensitive. Closes the duplicate-content exposure from a period when `home.html` was kept as scaffolding after Google had cached the old Bandzoogle `/home`. See [roadmap R3](../roadmap.md#r3-google-search-console-cleanup-open--done-2026-04-19). |

**Why Page Rules and not Redirect Rules:** this zone's Cloudflare UI currently exposes legacy Page Rules only (no modern Redirect Rules or Bulk Redirects menu). When that changes, we can migrate this single rule without behavior change.

**Verifying the `/home` rule:**

```bash
# Expect 301 with location https://www.liveradiodfw.com/
for u in \
  https://www.liveradiodfw.com/home \
  https://www.liveradiodfw.com/home.html \
  https://www.liveradiodfw.com/home/ \
  https://liveradiodfw.com/home \
  "https://www.liveradiodfw.com/home?utm_source=x" \
  https://www.liveradiodfw.com/Home; do
  curl -sI "$u" | head -2
  echo
done
```

## Monitoring

- [x] **UptimeRobot** (free) HEAD-request monitor on `https://www.liveradiodfw.com`, 5-minute interval, email alerts to `info@liveradiodfw.com` (pushes to Ray's phone + watch). Live since ~2026-04-16, formally closed [R2](../roadmap.md#r2-uptimerobot-monitoring-open--done-2026-04-19) on 2026-04-19.
- [ ] **Google Search Console** weekly crawl-error check
- [ ] Cloudflare Analytics dashboard (free) shows traffic + errors

## Incident history

- **2026-04-15 → 2026-04-16** — 12-hour outage during initial Cloudflare migration. See [../postmortems/](../postmortems/).
- **2026-04-17** — Calendar sync wiped hand-curated fields on `shows.json`. Fixed with non-destructive merge + strict parser. See [../postmortems/2026-04-17-sync-wipe.md](../postmortems/2026-04-17-sync-wipe.md).

## Key contacts & accounts

| Account | Purpose |
|---|---|
| **GoDaddy** | Registrar (nameservers only) |
| **Cloudflare** | DNS, CDN, SSL edge |
| **GitHub** (`TicoRicoRay`) | `liveradiodfw-site`, `liveradiodfw-marketing` |
| **Microsoft 365 / Outlook** | `info@liveradiodfw.com`, band calendar host |
| **Mailchimp** (server `us6`) | Campaigns, Venues audience, DKIM signer |
| **Google Search Console** | Two verified properties (apex + www) |
| **Google Business Profile** | Local search |
| **GigSalad, The Bash** | Third-party booking leads |
| **Marketing phone** | (469) 606-0798 |
| **Band email** | info@liveradiodfw.com |
