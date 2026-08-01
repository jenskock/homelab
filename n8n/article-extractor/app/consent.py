from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx

DEFAULT_GOLEM_COOKIE = "golem_consent20"
DEFAULT_GOLEM_VERSION = "|250101"


def _is_golem(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host == "golem.de" or host.endswith(".golem.de")


def resolve_golem_consent(client: httpx.Client, url: str) -> str:
    cookie_name = DEFAULT_GOLEM_COOKIE
    cookie_version = DEFAULT_GOLEM_VERSION

    try:
        probe = client.get(
            url,
            headers={"Accept": "text/html", "Accept-Language": "de-DE,de;q=0.9"},
            follow_redirects=True,
        )
        match = re.search(
            r"GolemConsent\.setCustomConfig\((\{.*?\})\)",
            probe.text,
            flags=re.DOTALL,
        )
        if match:
            name_m = re.search(r'"cookieName"\s*:\s*"([^"]+)"', match.group(1))
            ver_m = re.search(r'"cookieVersion"\s*:\s*"([^"]+)"', match.group(1))
            if name_m:
                cookie_name = name_m.group(1)
            if ver_m:
                cookie_version = ver_m.group(1)
    except httpx.HTTPError:
        pass

    return f"{cookie_name}=simple{cookie_version}"


def cookies_for_url(client: httpx.Client, url: str) -> str:
    if _is_golem(url):
        return resolve_golem_consent(client, url)
    return ""
