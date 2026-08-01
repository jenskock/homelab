from __future__ import annotations

from html import escape

from app.extract import ExtractedArticle


PRINT_CSS = """
@page { margin: 14mm; }
body {
  margin: 0;
  color: #111;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 11.5pt;
  line-height: 1.45;
}
h1 {
  font-size: 20pt;
  line-height: 1.2;
  margin: 0 0 0.35em;
}
h2 {
  font-size: 14pt;
  margin: 1.2em 0 0.4em;
  padding-top: 0.25em;
  border-top: 1px solid #bbb;
}
h3 { font-size: 12pt; margin: 1em 0 0.35em; }
p { margin: 0 0 0.75em; }
ul, ol { margin: 0 0 1em; padding-left: 1.2em; }
li { margin: 0 0 0.4em; }
.meta {
  font-family: sans-serif;
  font-size: 9pt;
  color: #444;
  margin: 0 0 1.2em;
}
.article {
  page-break-after: always;
}
.article:last-child {
  page-break-after: auto;
}
"""


def build_day_document(
    *,
    feed_title: str,
    target_day: str,
    articles: list[ExtractedArticle],
) -> str:
    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="de">',
        "<head>",
        '<meta charset="utf-8" />',
        f"<title>{escape(feed_title)} · {escape(target_day)}</title>",
        f"<style>{PRINT_CSS}</style>",
        "</head>",
        "<body>",
    ]

    for article in articles:
        meta_bits = [escape(target_day)]
        if article.byline:
            meta_bits.append(escape(article.byline))
        meta_bits.append(escape(article.url))
        parts.append('<section class="article">')
        parts.append(f"<h1>{escape(article.title)}</h1>")
        parts.append(f'<p class="meta">{" · ".join(meta_bits)}</p>')
        parts.append(article.html)
        parts.append("</section>")

    parts.extend(["</body>", "</html>"])
    return "\n".join(parts)
