"""
================================================================================
DSCA Explorer USGS Fetcher - Change Log
================================================================================

BEFORE:
-------
- fetch_usgs_layers fetched Earthquakes, Water, Elevated Volcanoes, CAP Alerts,
  Monitored Volcanoes, and GeoJSON Volcanoes sequentially.
- Each data type was processed one after another, resulting in slow performance.
- No parallelization for per-type fetching.

AFTER:
------
- fetch_usgs_layers now fetches all six USGS data types in parallel using
  ThreadPoolExecutor and get_optimal_workers() from utils.py.
- Each data type is processed concurrently, greatly improving speed.
- Progress callback is updated as each data type finishes.
- Error handling for individual data types is improved.
- Overall scalability and speed are significantly improved.

================================================================================
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..config import (
    USGS_HANS_BASE,
    USGS_EQ_BASE,
    USGS_WATER_BASE,
    HIFLD_HEADERS
)
from .utils import get_optimal_workers

def fetch_usgs_layers(progress_cb=None):
    layers = []
    errors = []
    data_types = [
        "earthquakes",
        "water",
        "elevated_volcanoes",
        "cap_alerts",
        "monitored_volcanoes",
        "geojson_volcanoes"
    ]
    total = len(data_types)
    max_workers = min(get_optimal_workers(), total)

    def fetch_earthquakes():
        result = []
        try:
            url = f"{USGS_EQ_BASE}?format=geojson&starttime=2024-01-01&minmagnitude=5"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                name = props.get("place") or "USGS Earthquake"
                desc = f"M{props.get('mag','')} - {props.get('place','')}"
                url = props.get("url") or ""
                result.append({
                    "name": name,
                    "type": "USGS Earthquake",
                    "endpoint": url,
                    "formats": "GeoJSON",
                    "properties": props,
                    "description": desc,
                    "url": url,
                    "series": "Earthquakes",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("earthquakes", str(e)))
            print(f"Error fetching USGS earthquakes: {e}")
        return result

    def fetch_water():
        result = []
        try:
            url = f"{USGS_WATER_BASE}?sites=01646500&parameterCd=00060&format=json"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for ts in data.get("value", {}).get("timeSeries", []):
                props = ts.get("sourceInfo", {})
                name = props.get("siteName") or "USGS Water Site"
                desc = props.get("siteCode", [{}])[0].get("value", "")
                url = f"https://waterdata.usgs.gov/nwis/uv?site_no={desc}"
                result.append({
                    "name": name,
                    "type": "USGS Water Site",
                    "endpoint": url,
                    "formats": "JSON",
                    "properties": props,
                    "description": desc,
                    "url": url,
                    "series": "Water Data",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("water", str(e)))
            print(f"Error fetching USGS water data: {e}")
        return result

    def fetch_elevated_volcanoes():
        result = []
        try:
            resp = requests.get(f"{USGS_HANS_BASE}/volcano/getElevatedVolcanoes", headers=HIFLD_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for v in data:
                name = v.get("volcanoName") or v.get("volcCode") or "USGS Volcano"
                desc = f"Alert: {v.get('currentColorCode','')}, {v.get('alertLevel','')}"
                url = f"https://volcanoes.usgs.gov/volcanoes/{v.get('volcCode','')}"
                result.append({
                    "name": name,
                    "type": "USGS Elevated Volcano",
                    "endpoint": url,
                    "formats": "JSON",
                    "properties": v,
                    "description": desc,
                    "url": url,
                    "series": "Elevated Volcanoes",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("elevated_volcanoes", str(e)))
            print(f"Error fetching USGS elevated volcanoes: {e}")
        return result

    def fetch_cap_alerts():
        result = []
        try:
            resp = requests.get(f"{USGS_HANS_BASE}/volcano/getCAPElevated", headers=HIFLD_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for v in data:
                name = v.get("volcanoName") or v.get("volcCode") or "USGS CAP Alert"
                desc = v.get("headline") or v.get("description") or ""
                url = v.get("capUrl") or ""
                result.append({
                    "name": name,
                    "type": "USGS CAP Alert",
                    "endpoint": url,
                    "formats": "JSON",
                    "properties": v,
                    "description": desc,
                    "url": url,
                    "series": "CAP Alerts",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("cap_alerts", str(e)))
            print(f"Error fetching USGS CAP alerts: {e}")
        return result

    def fetch_monitored_volcanoes():
        result = []
        try:
            resp = requests.get(f"{USGS_HANS_BASE}/volcano/getMonitoredVolcanoes", headers=HIFLD_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for v in data:
                name = v.get("volcanoName") or v.get("volcCode") or "USGS Monitored Volcano"
                desc = v.get("region") or ""
                url = f"https://volcanoes.usgs.gov/volcanoes/{v.get('volcCode','')}"
                result.append({
                    "name": name,
                    "type": "USGS Monitored Volcano",
                    "endpoint": url,
                    "formats": "JSON",
                    "properties": v,
                    "description": desc,
                    "url": url,
                    "series": "Monitored Volcanoes",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("monitored_volcanoes", str(e)))
            print(f"Error fetching USGS monitored volcanoes: {e}")
        return result

    def fetch_geojson_volcanoes():
        result = []
        try:
            geojson_url = "https://volcanoes.usgs.gov/feeds/vhp_volcano_info.geojson"
            resp = requests.get(geojson_url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                name = props.get("volcanoName") or props.get("volcCode") or props.get("id") or "USGS GeoJSON Volcano"
                desc = f"Alert: {props.get('currentColorCode','')}, {props.get('alertLevel','')}"
                url = f"https://volcanoes.usgs.gov/volcanoes/{props.get('volcCode','') or props.get('id','')}"
                result.append({
                    "name": name,
                    "type": "USGS GeoJSON Volcano",
                    "endpoint": url,
                    "formats": "GeoJSON",
                    "properties": props,
                    "description": desc,
                    "url": url,
                    "series": "GeoJSON Volcanoes",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("geojson_volcanoes", str(e)))
            print(f"Error fetching USGS GeoJSON volcanoes: {e}")
        return result

    fetch_funcs = {
        "earthquakes": fetch_earthquakes,
        "water": fetch_water,
        "elevated_volcanoes": fetch_elevated_volcanoes,
        "cap_alerts": fetch_cap_alerts,
        "monitored_volcanoes": fetch_monitored_volcanoes,
        "geojson_volcanoes": fetch_geojson_volcanoes
    }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_funcs[dt]): dt for dt in data_types}
        for idx, future in enumerate(as_completed(futures)):
            dt = futures[future]
            result = future.result()
            layers.extend(result)
            if progress_cb:
                progress_cb(int(((idx+1)/total)*100), f"USGS: {idx+1}/{total} data types")

    if errors:
        for dt, err in errors:
            print(f"Error fetching USGS {dt}: {err}")
        if progress_cb:
            progress_cb(100, f"USGS: Error(s) in {len(errors)} data type(s)")
    elif progress_cb:
        progress_cb(100, f"USGS: {len(layers)} layers")
    return layers
