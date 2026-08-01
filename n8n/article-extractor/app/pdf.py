from __future__ import annotations

import os

import httpx

GOTENBERG_URL = os.environ.get("GOTENBERG_URL", "http://n8n-gotenberg:3000").rstrip("/")

DEFAULT_PAPER = {
    "paperWidth": "6.2",
    "paperHeight": "8.25",
    "marginTop": "0.4",
    "marginBottom": "0.4",
    "marginLeft": "0.45",
    "marginRight": "0.45",
}


async def html_to_pdf(html: str, paper: dict[str, str] | None = None) -> bytes:
    fields = {**(paper or DEFAULT_PAPER)}
    files = {"files": ("index.html", html.encode("utf-8"), "text/html; charset=utf-8")}

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{GOTENBERG_URL}/forms/chromium/convert/html",
            data=fields,
            files=files,
        )
        response.raise_for_status()
        pdf = response.content
        if not pdf.startswith(b"%PDF"):
            raise RuntimeError(f"Gotenberg returned non-PDF ({len(pdf)} bytes)")
        return pdf
