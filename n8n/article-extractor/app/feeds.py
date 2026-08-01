from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import feedparser

BERLIN = ZoneInfo("Europe/Berlin")


def previous_berlin_day() -> str:
    return (datetime.now(BERLIN).date() - timedelta(days=1)).isoformat()


def entry_civil_day(entry: feedparser.FeedParserDict) -> str | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if not parsed:
            continue
        try:
            dt = datetime(*parsed[:6], tzinfo=timezone.utc).astimezone(BERLIN)
            return dt.date().isoformat()
        except (TypeError, ValueError, OverflowError):
            continue
    return None


def entries_for_day(feed_xml: str | bytes, target_day: str) -> list[dict[str, str]]:
    parsed = feedparser.parse(feed_xml)
    items: list[dict[str, str]] = []
    for entry in parsed.entries:
        link = (entry.get("link") or "").strip()
        if not link:
            continue
        day = entry_civil_day(entry)
        if day != target_day:
            continue
        items.append(
            {
                "title": (entry.get("title") or "").strip(),
                "url": link,
                "day": day,
                "published": (entry.get("published") or entry.get("updated") or "").strip(),
            }
        )
    return items
