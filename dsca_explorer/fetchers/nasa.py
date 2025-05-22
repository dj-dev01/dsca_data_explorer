# dsca_explorer/fetchers/nasa.py

import requests
from ..config import NASA_CMR

def fetch_nasa_layers(progress_cb=None):
    layers = []
    try:
        if progress_cb:
            progress_cb(0, "Fetching NASA Earthdata")
        url = f"{NASA_CMR}?keyword=MOD11A1"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        entries = data.get("feed", {}).get("entry", [])
        total = len(entries)
        for idx, c in enumerate(entries):
            name = c.get("title") or "NASA Earthdata"
            desc = c.get("summary", "")
            url = c.get("id", "")
            layers.append({
                "name": name,
                "type": "NASA Earthdata",
                "endpoint": url,
                "formats": "JSON",
                "properties": c,
                "description": desc,
                "url": url,
                "series": "NASA Earthdata"
            })
            if progress_cb and total > 0:
                progress_cb(int((idx/total)*100), f"NASA: {idx+1}/{total}")
        if progress_cb:
            progress_cb(100, f"NASA: {len(layers)} layers")
    except Exception as e:
        print(f"Error fetching NASA Earthdata: {e}")
        if progress_cb:
            progress_cb(100, "NASA: Error")
    return layers
