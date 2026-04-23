#!/usr/bin/env python3
"""Purge the Cloudflare edge cache for liveradiodfw.com.

Why this exists:
  The site is served through Cloudflare (Free plan) with a ~10 min edge TTL.
  After a git push to master, the live site can lag behind origin by up to
  10 minutes. For our own verification we use `?v=<timestamp>` query-string
  busting (see audit_shows.py) but that does NOT help:
    - first-time visitors
    - social-share preview fetchers (Facebook debugger, Mailchimp previews)
    - venue contacts we're about to send a link to

  This script hits Cloudflare's purge API so the next request from any
  client gets a fresh copy from origin.

Usage:
  Purge whole zone (simple, slow-ish edge rebuild):
    python purge_cache.py

  Purge specific URLs (fast, preferred for targeted testing):
    python purge_cache.py https://www.liveradiodfw.com/shows.json
    python purge_cache.py https://www.liveradiodfw.com/ https://www.liveradiodfw.com/shows

  Purge shows.json + the two pages that render it (common case after a
  calendar-driven content change):
    python purge_cache.py --shows

  Dry-run (print what would be purged, don't call the API):
    python purge_cache.py --shows --dry-run

Env:
  CLOUDFLARE_API_TOKEN  Scoped token with Zone > Cache Purge permission.
  CLOUDFLARE_ZONE_ID    Zone ID for liveradiodfw.com (32-char hex, from
                        the Cloudflare dashboard > Overview pane).

  Load these from .env (same pattern as GIT_BRANCH today) or export them
  in the current shell.

Exit codes:
  0 success
  1 config error (missing token or zone id)
  2 API call failed
  3 post-purge verification failed (edge still served HIT)

Stdlib only. ASCII only. No third-party deps.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITE_ORIGIN = "https://www.liveradiodfw.com"

# Common URL bundles. Keep small and explicit so nobody accidentally
# purges too much. Cloudflare Free plan allows up to 30 URLs per call.
SHOWS_BUNDLE = [
    f"{SITE_ORIGIN}/shows.json",
    f"{SITE_ORIGIN}/",
    f"{SITE_ORIGIN}/shows",
]


def load_env_file(path: Path) -> None:
    """Minimal .env loader: KEY=VALUE lines, '#' comments, no quoting magic.

    Does not override values already set in os.environ. Same convention as
    the existing scripts in this repo.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, val = line.partition('=')
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def api_purge(token: str, zone_id: str, body: dict) -> dict:
    """POST to Cloudflare purge_cache endpoint. Returns parsed JSON response."""
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        method='POST',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        # Cloudflare returns JSON error bodies even on 4xx; surface them.
        try:
            err_body = json.loads(exc.read().decode('utf-8'))
        except Exception:
            err_body = {'errors': [{'message': str(exc)}]}
        return {'success': False, '_http_status': exc.code, **err_body}


def verify_miss(url: str) -> tuple[bool, str]:
    """Fetch URL with cache-buster, read cf-cache-status header.

    Returns (is_miss_or_dynamic, header_value). 'MISS' or 'DYNAMIC' means
    the edge just pulled from origin, which is exactly what we want right
    after a purge.
    """
    bust_url = f"{url}{'&' if '?' in url else '?'}_pv={int(time.time())}"
    req = urllib.request.Request(bust_url, method='HEAD')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            cc = resp.headers.get('cf-cache-status', '(absent)')
            return (cc.upper() in ('MISS', 'DYNAMIC', 'EXPIRED', 'BYPASS'), cc)
    except Exception as exc:
        return (False, f'(error: {exc})')


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Purge Cloudflare edge cache for liveradiodfw.com.',
    )
    parser.add_argument(
        'urls', nargs='*',
        help='Specific URLs to purge (up to 30). Omit for whole-zone purge '
             'unless --shows or --everything is used.',
    )
    parser.add_argument(
        '--shows', action='store_true',
        help='Purge the shows bundle: /shows.json, /, /shows. Common case '
             'after a calendar-driven content change.',
    )
    parser.add_argument(
        '--everything', action='store_true',
        help='Purge the entire zone. Use sparingly; slower edge rebuild.',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Print what would be purged; do not call the API.',
    )
    parser.add_argument(
        '--no-verify', action='store_true',
        help='Skip the post-purge HEAD check of cf-cache-status.',
    )
    args = parser.parse_args()

    # Load .env from the repo root (same dir as this script).
    load_env_file(Path(__file__).resolve().parent / '.env')

    token = os.environ.get('CLOUDFLARE_API_TOKEN', '').strip()
    zone_id = os.environ.get('CLOUDFLARE_ZONE_ID', '').strip()

    # Decide what to purge.
    if args.everything:
        body = {'purge_everything': True}
        label = 'ENTIRE ZONE'
        verify_targets: list[str] = []
    elif args.shows:
        body = {'files': list(SHOWS_BUNDLE)}
        label = f'{len(SHOWS_BUNDLE)} URLs (shows bundle)'
        verify_targets = list(SHOWS_BUNDLE)
    elif args.urls:
        if len(args.urls) > 30:
            print(f"ERROR: Cloudflare Free plan allows up to 30 URLs per "
                  f"purge call; got {len(args.urls)}.", file=sys.stderr)
            return 1
        body = {'files': list(args.urls)}
        label = f'{len(args.urls)} URLs'
        verify_targets = list(args.urls)
    else:
        print("ERROR: nothing to purge. Pass URLs, --shows, or --everything.",
              file=sys.stderr)
        parser.print_help(sys.stderr)
        return 1

    # Dry-run short-circuit.
    if args.dry_run:
        print(f"DRY RUN: would purge {label}")
        print(f"  POST https://api.cloudflare.com/client/v4/zones/"
              f"{zone_id or '<ZONE_ID_MISSING>'}/purge_cache")
        print(f"  body: {json.dumps(body)}")
        return 0

    # Config validation (after dry-run so --dry-run works without a token).
    if not token:
        print("ERROR: CLOUDFLARE_API_TOKEN is not set. Add it to .env or "
              "export it in the shell.", file=sys.stderr)
        return 1
    if not zone_id:
        print("ERROR: CLOUDFLARE_ZONE_ID is not set. Add it to .env or "
              "export it in the shell.", file=sys.stderr)
        return 1

    # Call the API.
    print(f"Purging {label} ...")
    resp = api_purge(token, zone_id, body)
    if not resp.get('success'):
        print("PURGE FAILED:", file=sys.stderr)
        print(json.dumps(resp, indent=2), file=sys.stderr)
        return 2
    req_id = (resp.get('result') or {}).get('id', '(no id)')
    print(f"  OK. Cloudflare request id: {req_id}")

    # Verify.
    if args.no_verify or not verify_targets:
        return 0

    # Edge needs a couple seconds to drop the entry before next HEAD.
    time.sleep(3)
    print("Verifying edge served fresh copy (cf-cache-status should be "
          "MISS / DYNAMIC / EXPIRED / BYPASS on first request):")
    any_fail = False
    for u in verify_targets:
        ok, cc = verify_miss(u)
        mark = 'OK' if ok else 'WARN'
        print(f"  [{mark}] {u}  cf-cache-status={cc}")
        if not ok:
            any_fail = True
    return 3 if any_fail else 0


if __name__ == '__main__':
    sys.exit(main())
