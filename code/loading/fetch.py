from __future__ import annotations

import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT_SECONDS = 30


class FetchError(RuntimeError):
    pass


def fetch_html(url: str) -> str:
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-IN,en;q=0.9",
            },
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise FetchError(f"Request failed for {url}: {exc}") from exc

    if response.status_code != 200:
        raise FetchError(f"HTTP {response.status_code} for {url}")

    html = response.text or ""
    if not html.strip():
        raise FetchError(f"Empty HTTP body for {url}")
    return html
