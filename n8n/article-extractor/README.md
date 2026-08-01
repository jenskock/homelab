# article-extractor

Small FastAPI service that:

1. Resolves publisher consent cookies (Golem `golem_consent20`)
2. Fetches article HTML
3. Extracts the article body
4. Renders a clean daily PDF via Gotenberg

## Local test (no Docker)

```bash
cd n8n/article-extractor
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Consent cookie for a Golem URL
python cli.py consent 'https://www.golem.de/news/klimaanlagen-co-die-obskure-welt-der-internet-wunderprodukte-2607-211478.html'

# Extract one article → JSON summary or HTML file
python cli.py extract 'https://www.golem.de/news/klimaanlagen-co-die-obskure-welt-der-internet-wunderprodukte-2607-211478.html' -o /tmp/article.html

# All Internet-feed articles for a Berlin day
python cli.py feed 'https://rss.golem.de/rss.php?ms=internet&feed=RSS2.0' \
  --day 2026-07-31 --limit 5 -o /tmp/day.html
```

## Local API

```bash
export GOTENBERG_URL=http://127.0.0.1:3000   # optional for /v1/feed-day-pdf
uvicorn app.main:app --reload --port 8080

curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/v1/extract \
  -H 'content-type: application/json' \
  -d '{"url":"https://www.golem.de/news/klimaanlagen-co-die-obskure-welt-der-internet-wunderprodukte-2607-211478.html"}' \
  | jq .title

# Dry-run feed day (no PDF)
curl -s http://127.0.0.1:8080/v1/feed-day-meta \
  -H 'content-type: application/json' \
  -d '{"feed_url":"https://rss.golem.de/rss.php?ms=internet&feed=RSS2.0","day":"2026-07-31"}' | jq
```

## Docker

Started from `n8n/docker-compose.yml` as `article-extractor` on `http://article-extractor:8080`.

## n8n contract

`POST /v1/feed-day-pdf`

```json
{
  "feed_url": "https://rss.golem.de/rss.php?ms=internet&feed=RSS2.0",
  "day": "2026-07-31",
  "feed_title": "Golem-Internet",
  "max_articles": 25
}
```

- `200` + `application/pdf` when at least one article rendered
- `204` when the feed has no items for that day (n8n should skip upload)
- Headers: `X-Feed-Day`, `X-Article-Count`, `X-Failed-Count`
