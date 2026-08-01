from __future__ import annotations

import httpx

from app.consent import cookies_for_url
from app.extract import ExtractedArticle, extract_article

USER_AGENT = (
    "Mozilla/5.0 (compatible; homelab-article-extractor/1.0; +https://n8n.jenskock.de)"
)


def sync_client() -> httpx.Client:
    return httpx.Client(
        timeout=30.0,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        },
        follow_redirects=True,
    )


def fetch_and_extract(url: str) -> ExtractedArticle:
    with sync_client() as client:
        cookie = cookies_for_url(client, url)
        headers: dict[str, str] = {"Accept": "text/html,application/xhtml+xml"}
        if cookie:
            headers["Cookie"] = cookie
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return extract_article(response.text, str(response.url))
