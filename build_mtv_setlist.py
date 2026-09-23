#!/usr/bin/env python3
"""Refresh only the marked MTV set-list regions from the public BandHelper feed."""

import html
import math
import os
from pathlib import Path
import re
import tempfile
from datetime import date

import requests


FEED_URL = "https://www.bandhelper.com/feed/set_list/YIm52J"
PAGE_PATH = Path(__file__).resolve().parent / "i-want-my-mtv" / "index.html"
TIMEOUT = 20
MAX_FEED_BYTES = 1_000_000
HEADERS = {"User-Agent": "LiveRadioDFW-build/1.0", "Accept": "application/json"}

# Presentation only. BandHelper remains authoritative for membership and order.
# The opening title is Ray's stage wording; the other entries fix display spelling.
TITLE_LABELS = {
    ("money for nothing", "dire straits"): "I Want My MTV / Money for Nothing",
}
ARTIST_LABELS = {
    "cure": "The Cure",
    "motels": "The Motels",
    "human league": "The Human League",
    "billy idol": "Billy Idol",
    "bangles": "The Bangles",
    "j. giles band": "J. Geils Band",
    "madonna/future 86": "Madonna / Future 86",
}


def clean_text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Feed has a missing or invalid song title/artist")
    # Feed JSON includes HTML entities in strings. Decode once, then escape on output.
    return " ".join(html.unescape(value).split())


def parse_feed(payload):
    """Return public (title, artist) pairs in source order, excluding Extras."""
    if not isinstance(payload, list) or not payload:
        raise ValueError("Expected a nonempty BandHelper JSON array")
    songs = []
    extras = False
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Invalid BandHelper row")
        kind = item.get("type")
        if kind == "set":
            name = clean_text(item.get("name"))
            # Accept Extra, Extras, Extra's, and the typographic apostrophe variant.
            normalized = re.sub(r"[\s'\u2019]", "", name.casefold())
            extras = normalized in ("extra", "extras")
        elif kind == "song" and not extras:
            title = clean_text(item.get("name"))
            artist = clean_text(item.get("artist"))
            title = TITLE_LABELS.get((title.casefold(), artist.casefold()), title)
            artist = ARTIST_LABELS.get(artist.casefold(), artist)
            songs.append((title, artist))
        elif kind not in ("song", "break", "pause"):
            raise ValueError("Unrecognized BandHelper row type")
    if not songs:
        raise ValueError("Feed contains no main-set songs; keeping published list")
    if len(songs) > 200:
        raise ValueError("Unexpectedly large set list; keeping published list")
    return songs


def render_list(songs):
    rows = math.ceil(len(songs) / 2)
    lines = [
        f'        <ol class="setlist" aria-label="Official show running order" '
        f'style="--setlist-rows:{rows}">'
    ]
    for title, artist in songs:
        lines.append(
            '          <li><div><span class="song-title">'
            + html.escape(title)
            + '</span><span class="song-artist">'
            + html.escape(artist)
            + "</span></div></li>"
        )
    lines.append("        </ol>")
    return "\n" + "\n".join(lines) + "\n        "


def replace_region(page, name, content):
    start, end = f"<!-- BEGIN_MTV_{name} -->", f"<!-- END_MTV_{name} -->"
    if page.count(start) != 1 or page.count(end) != 1:
        raise ValueError(f"Expected exactly one pair of MTV_{name} markers")
    pattern = re.escape(start) + r".*?" + re.escape(end)
    result, count = re.subn(
        pattern, lambda match: start + content + end, page, flags=re.DOTALL
    )
    if count != 1:
        raise ValueError(f"Invalid MTV_{name} marker order")
    return result


def update_page(page, songs, today=None):
    # Validate all markers before any write, even when no song data changed.
    rendered = replace_region(page, "SETLIST", render_list(songs))
    noun = "selection" if len(songs) == 1 else "selections"
    rendered = replace_region(rendered, "COUNT", f"{len(songs)} {noun}")
    day = today or date.today()
    dated = replace_region(
        rendered, "DATE", f"{day.strftime('%B')} {day.day}, {day.year}"
    )
    # A date-only change must not create a daily commit.
    return page if rendered == page else dated


def sync_setlist(page_path=PAGE_PATH, fetch=None, today=None):
    """Fetch/validate fully, then atomically replace the page. Return changed bool.

    Raises on failure, leaving the last-good page untouched. Only title/artist
    strings enter public HTML; internal BandHelper metadata is never persisted.
    """
    page_path = Path(page_path)
    response = (fetch or requests.get)(FEED_URL, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    if len(response.content) > MAX_FEED_BYTES:
        raise ValueError("BandHelper response exceeds size limit")
    songs = parse_feed(response.json())
    current = page_path.read_text(encoding="utf-8")
    updated = update_page(current, songs, today)
    if current == updated:
        return False
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=page_path.parent, prefix=".mtv-", suffix=".tmp", delete=False
        ) as temp:
            temp_path = Path(temp.name)
            temp.write(updated)
        os.chmod(temp_path, page_path.stat().st_mode)
        os.replace(temp_path, page_path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    return True


def main():
    try:
        changed = sync_setlist()
    except (requests.RequestException, ValueError, OSError) as exc:
        print(f"[mtv] ERROR: {exc}")
        return 1
    print("[mtv] UPDATED official set list" if changed else "[mtv] cache hit, no change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
