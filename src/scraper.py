from __future__ import annotations

from datetime import datetime, timezone
from time import sleep

import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    ),
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
}


def fetch_html(url: str, retries: int = 3, timeout: int = 15) -> tuple[str, datetime]:
    """Fetch HTML with a small retry loop and return the scrape timestamp."""
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            response.raise_for_status()
            if not response.text.strip():
                raise ValueError("Trang nguồn trả về nội dung rỗng.")
            return response.text, datetime.now(timezone.utc)
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                sleep(1.5 * attempt)

    raise RuntimeError(f"Không thể lấy dữ liệu từ Webgia sau {retries} lần thử: {last_error}")
