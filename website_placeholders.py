"""Display-only private cards, separate from calendar bookings and history."""

import json
from datetime import date, datetime


def load_placeholders(path, confirmed_shows, today=None):
    """Return future private cards; a real show always wins on the same date."""
    today = today or date.today()
    if not path.exists():
        return []
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("Website placeholders must be a list")
    occupied = {show["date"] for show in confirmed_shows}
    cards = []
    for entry in entries:
        day = date.fromisoformat(entry["date"])
        time = entry["time"]
        datetime.strptime(time, "%I:%M %p")  # Validate before HTML rendering.
        if day < today or day.isoformat() in occupied:
            continue
        occupied.add(day.isoformat())
        cards.append({
            "date": day.isoformat(),
            "day_name": day.strftime("%a"),
            "day_num": str(day.day),
            "month": day.strftime("%b"),
            "time": time,
            "title": "Private Event",
            "venue": "Private Event",
            "address": "",
            "address_short": "",
            "maps_url": "",
            "private": True,
            "website_placeholder": True,
        })
    return sorted(cards, key=lambda show: show["date"])
