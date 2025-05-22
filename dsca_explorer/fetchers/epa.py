# dsca_explorer/fetchers/epa.py

import requests
from ..config import EPA_BASE

def fetch_epa_layers(progress_cb=None):
    layers = []
    try:
        if progress_cb:
            progress_cb(0, "Fetching EPA Water Systems")
        url = f"{EPA_BASE}/WATER_SYSTEM/STATE/CA/ROWS/0:10/JSON"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for ws in data:
            name = ws.get("PWS_NAME") or "EPA Water System"
            desc = ws.get("PWS_ACTIVITY_CODE", "")
            url = "https://enviro.epa.gov/"
            layers.append({
                "name": name,
                "type": "EPA Water System",
                "endpoint": url,
                "formats": "JSON",
                "properties": ws,
                "description": desc,
                "url": url,
                "series": "EPA Water"
            })
        if progress_cb:
            progress_cb(100, f"EPA: {len(layers)} layers")
    except Exception as e:
        print(f"Error fetching EPA water systems: {e}")
        if progress_cb:
            progress_cb(100, "EPA: Error")
    return layers
