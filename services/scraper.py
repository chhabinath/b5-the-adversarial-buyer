import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import httpx

CACHE_DIR = Path("./cache/scrapes")


def _get_cache_path(url: str) -> Path:
    url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{url_hash}.json"


def fetch_page(url: str) -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _get_cache_path(url)

    if cache_file.exists():
        print(f"[CACHE HIT] {url}")
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["content"]

    print(f"[FETCHING FRESH] {url} via Jina Reader...")
    jina_url = f"https://r.jina.ai/{url}"

    last_error = None
    for attempt in range(2):
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(jina_url)
                response.raise_for_status()
                content = response.text

                payload = {
                    "url": url,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "content": content,
                }
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)

                return content
        except Exception as e:
            last_error = e
            if attempt == 0:
                print(f"[RETRY] Request failed for {url}: {e}. Retrying in 2s...")
                time.sleep(2)

    raise RuntimeError(
        f"Failed to fetch page from Jina Reader for URL '{url}' after 2 attempts: {last_error}"
    )
