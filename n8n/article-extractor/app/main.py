from __future__ import annotations

import logging
import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, HttpUrl

from app.extract import ExtractedArticle
from app.feeds import entries_for_day, previous_berlin_day
from app.fetch import fetch_and_extract, sync_client
from app.html_doc import build_day_document
from app.pdf import html_to_pdf

logger = logging.getLogger("article-extractor")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "25"))

app = FastAPI(title="article-extractor", version="1.0.0")


class ExtractRequest(BaseModel):
    url: HttpUrl


class ExtractResponse(BaseModel):
    title: str
    url: str
    html: str
    byline: str | None = None
    published: str | None = None


class FeedDayPdfRequest(BaseModel):
    feed_url: HttpUrl
    day: str | None = None
    feed_title: str = "News"
    max_articles: int = Field(default=MAX_ARTICLES, ge=1, le=50)


class FeedDayPdfMeta(BaseModel):
    day: str
    feed_url: str
    article_count: int
    failed: list[dict[str, str]]
    titles: list[str]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest) -> ExtractResponse:
    try:
        article = fetch_and_extract(str(req.url))
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    except httpx.HTTPError as err:
        raise HTTPException(status_code=502, detail=f"fetch failed: {err}") from err

    return ExtractResponse(
        title=article.title,
        url=article.url,
        html=article.html,
        byline=article.byline,
        published=article.published,
    )


@app.post("/v1/feed-day-pdf")
async def feed_day_pdf(req: FeedDayPdfRequest) -> Response:
    target_day = req.day or previous_berlin_day()
    feed_url = str(req.feed_url)

    with sync_client() as client:
        try:
            feed_resp = client.get(
                feed_url,
                headers={
                    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
                },
            )
            feed_resp.raise_for_status()
        except httpx.HTTPError as err:
            raise HTTPException(status_code=502, detail=f"feed fetch failed: {err}") from err

        entries = entries_for_day(feed_resp.content, target_day)[: req.max_articles]

    if not entries:
        return Response(
            status_code=204,
            headers={"X-Feed-Day": target_day, "X-Article-Count": "0"},
        )

    articles: list[ExtractedArticle] = []
    failed: list[dict[str, str]] = []

    for entry in entries:
        try:
            articles.append(fetch_and_extract(entry["url"]))
        except Exception as err:
            logger.warning("extract failed for %s: %s", entry["url"], err)
            failed.append({"url": entry["url"], "error": str(err)})

    if not articles:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "all article extractions failed",
                "day": target_day,
                "failed": failed,
            },
        )

    document = build_day_document(
        feed_title=req.feed_title,
        target_day=target_day,
        articles=articles,
    )

    try:
        pdf = await html_to_pdf(document)
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"pdf render failed: {err}") from err

    filename = f"{req.feed_title}-{target_day}.pdf".replace(" ", "-")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Feed-Day": target_day,
            "X-Article-Count": str(len(articles)),
            "X-Failed-Count": str(len(failed)),
        },
    )


@app.post("/v1/feed-day-meta", response_model=FeedDayPdfMeta)
def feed_day_meta(req: FeedDayPdfRequest) -> FeedDayPdfMeta:
    target_day = req.day or previous_berlin_day()
    with sync_client() as client:
        feed_resp = client.get(str(req.feed_url))
        feed_resp.raise_for_status()
        entries = entries_for_day(feed_resp.content, target_day)[: req.max_articles]

    titles: list[str] = []
    failed: list[dict[str, str]] = []
    for entry in entries:
        try:
            titles.append(fetch_and_extract(entry["url"]).title)
        except Exception as err:
            failed.append({"url": entry["url"], "error": str(err)})

    return FeedDayPdfMeta(
        day=target_day,
        feed_url=str(req.feed_url),
        article_count=len(titles),
        failed=failed,
        titles=titles,
    )
