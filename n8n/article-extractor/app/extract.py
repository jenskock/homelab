from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag

CUT_CLASS_MARKERS = (
    "go-pagination",
    "go-article-footer",
    "go-tag-list",
    "go-affiliate",
    "go-button-bar",
    "go-overflowmenu",
    "go-index",
    "go-teaser",
)

ALLOWED_TAGS = {"h1", "h2", "h3", "h4", "p", "ul", "ol", "li", "blockquote", "em", "strong", "a", "br"}
WRAPPER_TAGS = {"div", "section", "header", "span"}


@dataclass(frozen=True)
class ExtractedArticle:
    title: str
    html: str
    url: str
    byline: str | None = None
    published: str | None = None


def _absolute_urls(root: Tag, base_url: str) -> None:
    for tag in root.find_all("a"):
        href = tag.get("href")
        if href:
            tag["href"] = urljoin(base_url, href)


def _strip_noise(root: Tag) -> None:
    for tag in root.find_all(
        ["script", "style", "noscript", "iframe", "svg", "form", "img", "figure", "picture", "source", "video", "audio"]
    ):
        tag.decompose()

    to_remove: list[Tag] = []
    for tag in root.find_all(True):
        classes = " ".join(tag.get("class") or [])
        if any(m in classes for m in CUT_CLASS_MARKERS) or tag.name in {"nav", "aside"}:
            to_remove.append(tag)
    for tag in to_remove:
        tag.decompose()


def _cut_after_markers(root: Tag) -> None:
    for tag in root.find_all(True):
        classes = " ".join(tag.get("class") or [])
        if any(m in classes for m in ("go-pagination", "go-article-footer", "go-tag-list")):
            for sibling in list(tag.next_siblings):
                if isinstance(sibling, (Tag, NavigableString)):
                    sibling.extract()
            tag.decompose()
            return


def _text(el: Tag | None) -> str:
    if not el:
        return ""
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def extract_article(html: str, url: str) -> ExtractedArticle:
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("h1")
    if title_tag and "Willkommen auf Golem" in title_tag.get_text():
        raise ValueError("Golem consent interstitial — cookie missing/invalid")

    article = soup.select_one("article.go-article") or soup.find("article")
    if not article:
        raise ValueError(f"No <article> found at {url}")

    title = _text(article.select_one("h1")) or _text(soup.find("h1")) or "Untitled"
    byline = _text(article.select_one(".go-article-header__byline")) or None
    intro = _text(article.select_one(".go-article-header__intro")) or None
    published = _text(article.select_one(".go-article-header__meta")) or None

    _strip_noise(article)
    _cut_after_markers(article)
    _absolute_urls(article, url)

    for tag in list(article.find_all(True)):
        if tag.name in ALLOWED_TAGS:
            continue
        if tag.name in WRAPPER_TAGS:
            tag.unwrap()
        else:
            tag.decompose()

    body_html = "".join(str(c) for c in article.children if str(c).strip())
    body_html = re.sub(r"\s*HTML_TAG_(?:START|END)\s*", " ", body_html)
    body_html = re.sub(r"\s{2,}", " ", body_html)
    if intro and intro not in body_html:
        body_html = f"<p><em>{intro}</em></p>" + body_html

    return ExtractedArticle(
        title=unescape(title),
        html=body_html,
        url=url,
        byline=byline,
        published=published,
    )
