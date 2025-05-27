"""
================================================================================
DSCA Explorer NASA Fetcher - Change Log
================================================================================

BEFORE:
-------
- fetch_nasa_layers fetched NASA Earthdata entries for a single keyword ("MOD11A1")
  in a single HTTP request.
- No parallelization; only one keyword fetched per call.

AFTER:
------
- fetch_nasa_layers now supports fetching NASA Earthdata entries for multiple
  keywords in parallel using ThreadPoolExecutor and get_optimal_workers() from utils.py.
- Each keyword is processed concurrently, improving speed if multiple keywords are used.
- Progress callback is updated as each keyword finishes.
- Error handling for individual keywords is improved.
- If only one keyword is used, behavior is unchanged.

================================================================================
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..config import NASA_CMR
from .utils import get_optimal_workers

def fetch_nasa_layers(progress_cb=None, keywords=None):
    """
    Fetch NASA Earthdata layers for one or more keywords in parallel.
    By default, fetches only for "MOD11A1".
    """
    if keywords is None:
        keywords = ["MOD11A1"]

    layers = []
    errors = []
    max_workers = get_optimal_workers()
    total = len(keywords)

    def fetch_keyword(keyword):
        url = f"{NASA_CMR}?keyword={keyword}"
        keyword_layers = []
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            entries = data.get("feed", {}).get("entry", [])
            for c in entries:
                name = c.get("title") or "NASA Earthdata"
                desc = c.get("summary", "")
                entry_url = c.get("id", "")
                keyword_layers.append({
                    "name": name,
                    "type": "NASA Earthdata",
                    "endpoint": entry_url,
                    "formats": "JSON",
                    "properties": c,
                    "description": desc,
                    "url": entry_url,
                    "series": "NASA Earthdata",
                    "source": "NASA"
                })
        except Exception as e:
            errors.append((keyword, str(e)))
            print(f"Error fetching NASA Earthdata for keyword '{keyword}': {e}")
        return keyword_layers

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_keyword, kw): kw for kw in keywords}
        for idx, future in enumerate(as_completed(futures)):
            keyword_layers = future.result()
            layers.extend(keyword_layers)
            if progress_cb:
                progress_cb(int(((idx+1)/total)*100), f"NASA: {idx+1}/{total} keywords")

    if errors:
        for keyword, err in errors:
            print(f"Error fetching NASA Earthdata for keyword '{keyword}': {err}")
        if progress_cb:
            progress_cb(100, f"NASA: Error(s) in {len(errors)} keyword(s)")
    elif progress_cb:
        progress_cb(100, f"NASA: {len(layers)} layers")

    return layers
