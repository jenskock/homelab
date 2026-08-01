#!/usr/bin/env python3
"""Local CLI for consent/extract checks without Docker."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.consent import cookies_for_url  # noqa: E402
from app.feeds import entries_for_day, previous_berlin_day  # noqa: E402
from app.fetch import fetch_and_extract, sync_client  # noqa: E402
from app.html_doc import build_day_document  # noqa: E402


def cmd_extract(args: argparse.Namespace) -> int:
    article = fetch_and_extract(args.url)
    if args.out:
        Path(args.out).write_text(
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>{article.title}</title></head>"
            f"<body><h1>{article.title}</h1>{article.html}</body></html>",
            encoding="utf-8",
        )
        print(f"wrote {args.out} ({article.title!r})")
    else:
        print(
            json.dumps(
                {
                    "title": article.title,
                    "url": article.url,
                    "byline": article.byline,
                    "published": article.published,
                    "html_bytes": len(article.html),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


def cmd_feed(args: argparse.Namespace) -> int:
    day = args.day or previous_berlin_day()
    with sync_client() as client:
        resp = client.get(args.feed_url)
        resp.raise_for_status()
        entries = entries_for_day(resp.content, day)[: args.limit]

    print(f"day={day} entries={len(entries)}")
    articles = []
    for entry in entries:
        try:
            art = fetch_and_extract(entry["url"])
            print(f"  OK  {art.title}")
            articles.append(art)
        except Exception as err:
            print(f"  ERR {entry['url']}: {err}")

    if args.out and articles:
        doc = build_day_document(
            feed_title=args.title or "Feed",
            target_day=day,
            articles=articles,
        )
        Path(args.out).write_text(doc, encoding="utf-8")
        print(f"wrote {args.out}")
    return 0


def cmd_consent(args: argparse.Namespace) -> int:
    with sync_client() as client:
        print(cookies_for_url(client, args.url))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="article-extractor local tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_extract = sub.add_parser("extract", help="Extract one article")
    p_extract.add_argument("url")
    p_extract.add_argument("-o", "--out", help="Write HTML file")
    p_extract.set_defaults(func=cmd_extract)

    p_feed = sub.add_parser("feed", help="Extract articles for a Berlin calendar day")
    p_feed.add_argument("feed_url")
    p_feed.add_argument("--day", help="YYYY-MM-DD (default: yesterday Berlin)")
    p_feed.add_argument("--limit", type=int, default=10)
    p_feed.add_argument("--title", default="Feed")
    p_feed.add_argument("-o", "--out", help="Write combined HTML")
    p_feed.set_defaults(func=cmd_feed)

    p_consent = sub.add_parser("consent", help="Show consent Cookie header for a URL")
    p_consent.add_argument("url")
    p_consent.set_defaults(func=cmd_consent)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
