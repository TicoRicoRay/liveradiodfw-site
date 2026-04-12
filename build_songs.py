#!/usr/bin/env python3
"""
build_songs.py — BandHelper Song Cache Builder
LiveRadioDFW site build helper

At build time:
  - Fetch each BandHelper widget URL (returns JS document.write snippets)
  - Convert JS widget to clean HTML fragment
  - Compare MD5 hash against stored cache
  - If changed (or no cache): save new HTML + update hash
  - If unchanged: print "cache hit, skipping"
  - Print summary of what changed

Usage:
    python3 build_songs.py [--force]

Options:
    --force   Ignore stored hashes and re-fetch/re-save everything
"""

import requests
import re
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

URLS = {
    "all":     "https://www.bandhelper.com/widget/smart_list/4rBNT6/13881?layout=2&fields=artist&sections=0&labels=0",
    "80s":     "https://www.bandhelper.com/widget/smart_list/doTsnc/13881?layout=2&fields=artist&sections=0&labels=0",
    "70s":     "https://www.bandhelper.com/widget/smart_list/diw3wK/13881?layout=2&fields=artist&sections=0&labels=0",
    "classic": "https://www.bandhelper.com/widget/smart_list/CJzlvQ/13881?layout=2&fields=artist&sections=0&labels=0",
    "oldies":  "https://www.bandhelper.com/widget/smart_list/AEqwak/13881?layout=2&fields=artist&sections=0&labels=0",
}

FILE_MAP = {
    "all":     "songs-all.html",
    "80s":     "songs-80s.html",
    "70s":     "songs-70s.html",
    "classic": "songs-classic.html",
    "oldies":  "songs-oldies.html",
}

LABEL_MAP = {
    "all":     "All Songs",
    "80s":     "80s Station",
    "70s":     "70s Station",
    "classic": "Classic Rock",
    "oldies":  "Oldies",
}

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR    = os.path.join(SCRIPT_DIR, "cache")
HASH_FILE    = os.path.join(CACHE_DIR, "songs-hash.json")

# Map cache keys to the HTML page that should be stamped
PAGE_MAP = {
    "all":     "songs.html",
    "80s":     "the-all-80s-hits-station.html",
    "70s":     "the-all-70s-no-disco-hits-station.html",
    "classic": "the-classic-rock-station.html",
    "oldies":  "the-all-oldies-hits-station.html",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LiveRadioDFW-build/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = 20  # seconds

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def js_to_html(js_text: str) -> str:
    """
    BandHelper widgets are served as JavaScript document.write() calls.
    This function extracts the quoted strings and reconstructs the raw HTML.

    Example input line:
        document.write("<span class=\"bandhelper_name\">Roam</span><br />\\n");

    The function handles:
      - Escaped double quotes  \"  → "
      - Escaped forward slashes \\/  → /
      - Escaped newlines \\n → actual newlines
      - Escaped tabs \\t → actual tabs
      - Double backslashes \\\\ → single backslash
    """
    pattern = r'document\.write\("((?:[^"\\]|\\.)*)"\);'
    parts = re.findall(pattern, js_text)

    def unescape(s: str) -> str:
        return (s
            .replace('\\"', '"')
            .replace('\\/', '/')
            .replace('\\n', '\n')
            .replace('\\t', '\t')
            .replace('\\\\', '\\')
        )

    return "".join(unescape(p) for p in parts)


def md5_of(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def load_hashes() -> dict:
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return json.load(f)
    return {}


def save_hashes(hashes: dict) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(HASH_FILE, "w") as f:
        json.dump(hashes, f, indent=2)


def count_songs(html: str) -> int:
    return html.count('class="bandhelper_name"')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    force = "--force" in sys.argv

    os.makedirs(CACHE_DIR, exist_ok=True)
    stored_hashes = {} if force else load_hashes()

    new_hashes   = dict(stored_hashes)  # start from current, update as we go
    changed      = []
    cache_hits   = []
    errors       = []

    print(f"[build_songs] BandHelper cache check — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    if force:
        print("[build_songs] --force flag set: ignoring stored hashes\n")

    for key in URLS:
        label = LABEL_MAP[key]
        url   = URLS[key]
        dest  = os.path.join(CACHE_DIR, FILE_MAP[key])

        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            raw  = r.text
            html = js_to_html(raw)
            current_md5 = md5_of(raw)

            if not force and stored_hashes.get(key) == current_md5 and os.path.exists(dest):
                print(f"  [{key}] cache hit, skipping  ({label})")
                cache_hits.append(key)
            else:
                reason = "forced" if force else ("no cache" if key not in stored_hashes else "content changed")
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(html)
                new_hashes[key] = current_md5
                songs = count_songs(html)
                print(f"  [{key}] UPDATED ({reason}) — {songs} songs saved → {FILE_MAP[key]}")
                changed.append(key)

        except requests.RequestException as exc:
            print(f"  [{key}] ERROR fetching {url}: {exc}")
            errors.append((key, str(exc)))

    # Persist updated hashes only if something changed
    if changed:
        save_hashes(new_hashes)
        print(f"\n[build_songs] Hash file updated: {HASH_FILE}")

    # Summary
    print(f"\n[build_songs] Summary:")
    print(f"  Updated : {len(changed)}  ({', '.join(changed) if changed else 'none'})")
    print(f"  Cached  : {len(cache_hits)}  ({', '.join(cache_hits) if cache_hits else 'none'})")
    print(f"  Errors  : {len(errors)}  ({', '.join(k for k,_ in errors) if errors else 'none'})")

    # Stamp cached HTML into song pages
    print("\n[build_songs] Stamping cached HTML into song pages...")
    for key, page_file in PAGE_MAP.items():
        cache_file = os.path.join(CACHE_DIR, FILE_MAP[key])
        page_path  = os.path.join(SCRIPT_DIR, page_file)
        if not os.path.exists(cache_file):
            print(f"  [{key}] SKIP — cache file missing: {cache_file}")
            continue
        if not os.path.exists(page_path):
            print(f"  [{key}] SKIP — page not found: {page_file}")
            continue

        cached_html = open(cache_file, encoding="utf-8").read()
        # Clean up br tags so CSS inline display works correctly
        cached_html = cached_html.replace('<br />', '').replace('<br/>', '').replace('<br>', '')
        # Remove the inline font-family style BandHelper injects (site CSS handles this)
        cached_html = re.sub(r'<style[^>]*>.*?</style>', '', cached_html, flags=re.DOTALL)

        page_content = open(page_path, encoding="utf-8").read()
        if '<!-- BEGIN_SONGS -->' not in page_content:
            print(f"  [{key}] SKIP — no BEGIN_SONGS marker in {page_file}")
            continue

        new_content = re.sub(
            r'<!-- BEGIN_SONGS -->.*?<!-- END_SONGS -->',
            '<!-- BEGIN_SONGS -->\n' + cached_html.strip() + '\n<!-- END_SONGS -->',
            page_content,
            flags=re.DOTALL
        )
        if new_content != page_content:
            open(page_path, 'w', encoding="utf-8").write(new_content)
            print(f"  [{key}] stamped → {page_file}")
        else:
            print(f"  [{key}] no change in {page_file}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
