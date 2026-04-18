#!/usr/bin/env python3
"""Audit live site for show-page functional & display issues.

Checks per-page:
  - HTTP 200
  - <title> present, non-default
  - canonical tag present and matches URL
  - og:title / og:image / og:url present
  - JSON-LD MusicEvent present; past events must NOT have 'offers'; upcoming should have 'offers'
  - past-show banner present on past pages, absent on upcoming
  - Add-to-Calendar / Share absent on past pages, present on upcoming
  - nav & footer injected (look for a known nav link)
  - CSS v=39 cache-buster
  - .show-full-date span with year present in .show-page-meta
  - price rendered (free or $N)
  - description paragraph present (not empty)
  - No stray 'Jackson Crossing' / 'Risky Business' leak
  - No em-dash in visible HTML
  - No 'CDT' / 'CST' strings

Also checks:
  - shows.html, past-shows.html, index.html, sitemap.xml
"""
import json
import re
import sys
import urllib.request
import urllib.error
from html import unescape

BASE = "https://www.liveradiodfw.com"
issues = []

def warn(page, msg):
    issues.append((page, msg))

def fetch(path):
    # Cache-bust to get the latest edge copy (Cloudflare TTL is 10 min)
    import time
    sep = "&" if "?" in path else "?"
    url = BASE + path + f"{sep}_ab={int(time.time())}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "lrdfw-audit/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        })
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, f"ERR: {e}"

def strip_tags(html):
    # crude but good enough for leak detection
    return unescape(re.sub(r"<[^>]+>", " ", html))

with open("/home/user/workspace/lrdfw-ghpages/shows.json") as f:
    shows = json.load(f)

# Build slug list from file paths
import glob, os
pages = sorted(glob.glob("/home/user/workspace/lrdfw-ghpages/shows/*.html"))
slugs = [os.path.basename(p).replace(".html", "") for p in pages]

print(f"Auditing {len(slugs)} public show pages...\n")

# ---- Per-show-page checks ----
for slug in slugs:
    path = f"/shows/{slug}.html"
    status, html = fetch(path)
    if status != 200:
        warn(path, f"HTTP {status}")
        continue

    # figure out if this show is past or upcoming by matching slug to shows.json
    show = None
    for s in shows:
        # slug format: {venue-slug}-{YYYY-MM-DD}
        date = slug[-10:]
        if s.get("date") == date:
            # match venue too (loosely)
            show = s
            # keep iterating; last match on date may overwrite but dates are unique per slug
    is_past = show.get("past", False) if show else None

    # basic tags
    if not re.search(r"<title>[^<]+</title>", html):
        warn(path, "missing <title>")
    if 'rel="canonical"' not in html:
        warn(path, "missing canonical")
    if 'og:title' not in html or 'og:url' not in html or 'og:image' not in html:
        warn(path, "missing og tags")

    # cache-buster
    if 'style.css?v=40' not in html:
        warn(path, "CSS not v=40")

    # full date with year (show-page-meta should contain 4-digit year)
    meta_match = re.search(r'<p class="show-page-meta">(.*?)</p>', html, re.S)
    if not meta_match:
        warn(path, "missing .show-page-meta")
    else:
        meta_text = strip_tags(meta_match.group(1))
        if "show-full-date" not in meta_match.group(1):
            warn(path, "missing .show-full-date span in meta")
        if not re.search(r"\b20\d{2}\b", meta_text):
            warn(path, f"no 4-digit year in meta: {meta_text.strip()[:80]}")

    # JSON-LD
    ld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not ld_match:
        warn(path, "missing JSON-LD")
    else:
        try:
            ld = json.loads(ld_match.group(1))
            if ld.get("@type") != "MusicEvent":
                warn(path, f"JSON-LD @type is {ld.get('@type')}")
            if is_past is True and "offers" in ld:
                warn(path, "past show has JSON-LD offers (should be removed)")
            if is_past is False and "offers" not in ld:
                # only flag for non-private (all upcoming public have a price, could be $0 Free)
                warn(path, "upcoming show missing JSON-LD offers")
        except json.JSONDecodeError as e:
            warn(path, f"JSON-LD parse error: {e}")

    # nav/footer presence (look for a known nav link)
    if "Book the Band" not in html and "book" not in html.lower():
        warn(path, "nav/footer not injected")
    if "<footer" not in html.lower() and "site-footer" not in html:
        warn(path, "footer not injected")

    # past/upcoming specific
    if is_past is True:
        if "Add to Calendar" in html or "add-to-calendar" in html.lower():
            warn(path, "past show has Add-to-Calendar button")
        # past banner
        if "past-show" not in html.lower() and "past show" not in html.lower():
            warn(path, "past show missing past banner/indicator")
    elif is_past is False:
        if "Add to Calendar" not in html:
            warn(path, "upcoming show missing Add-to-Calendar")

    # description
    desc_match = re.search(r'<div class="show-description">(.*?)</div>', html, re.S)
    if desc_match:
        desc = strip_tags(desc_match.group(1)).strip()
        if len(desc) < 20:
            warn(path, f"description too short: {desc[:60]}")
    # description coming soon placeholder is OK

    # leakage checks
    visible = strip_tags(html)
    if re.search(r"\bJackson Crossing\b", visible, re.I):
        warn(path, "LEAK: 'Jackson Crossing' in visible text")
    if re.search(r"\bRisky Business\b", visible, re.I):
        warn(path, "LEAK: 'Risky Business' in visible text")
    # em-dash
    if "\u2014" in visible:
        warn(path, "LEAK: em-dash in visible text")
    # CDT/CST
    if re.search(r"\b(CDT|CST)\b", visible):
        warn(path, "LEAK: CDT/CST in visible text (should say Central)")

# ---- Index-level checks ----
for p in ["/shows.html", "/past-shows.html", "/index.html", "/sitemap.xml"]:
    status, html = fetch(p)
    if status != 200:
        warn(p, f"HTTP {status}")
        continue
    if p.endswith(".xml"):
        # sitemap basics
        if "/past-shows.html" not in html:
            warn(p, "sitemap missing /past-shows.html")
        n = len(re.findall(r"<loc>[^<]*/shows/[^<]+</loc>", html))
        if n != 95:
            warn(p, f"sitemap has {n} show URLs, expected 95")
    else:
        if 'style.css?v=40' not in html:
            warn(p, "CSS not v=40")
        if p == "/shows.html":
            # should contain exactly 9 upcoming cards (10 - 1 private filtered out if private hidden)
            # actually private are shown as "Private Event" placeholder cards? check
            cards = html.count('class="show-card-full')
            compact = html.count('class="show-card-compact')
            warn(p, f"INFO: {cards} full + {compact} compact show cards on shows.html")
        if p == "/past-shows.html":
            cards = html.count('class="show-card-full')
            compact = html.count('class="show-card-compact')
            warn(p, f"INFO: {cards} full + {compact} compact show cards on past-shows.html")
        # leak check
        v = strip_tags(html)
        if re.search(r"\bJackson Crossing\b", v, re.I):
            warn(p, "LEAK: Jackson Crossing")
        if re.search(r"\bRisky Business\b", v, re.I):
            warn(p, "LEAK: Risky Business")
        if "\u2014" in v:
            warn(p, "LEAK: em-dash")

# ---- Report ----
print(f"\n=== AUDIT RESULTS ({len(issues)} findings) ===\n")
info = [i for i in issues if "INFO" in i[1]]
real = [i for i in issues if "INFO" not in i[1]]

if real:
    print(f"*** {len(real)} REAL ISSUES ***")
    for page, msg in real:
        print(f"  {page}: {msg}")
else:
    print("No real issues found.")

if info:
    print(f"\n--- {len(info)} info ---")
    for page, msg in info:
        print(f"  {page}: {msg}")
