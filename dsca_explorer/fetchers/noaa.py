"""
================================================================================
DSCA Explorer NOAA Fetcher - Change Log
================================================================================

BEFORE:
-------
- fetch_noaa_layers fetched NOAA Alerts, Stations, Radar, and Tides sequentially.
- Each data type was processed one after another, resulting in slow performance.
- No parallelization for per-type fetching.

AFTER:
------
- fetch_noaa_layers now fetches NOAA Alerts, Stations, Radar, and Tides in parallel
  using ThreadPoolExecutor and get_optimal_workers() from utils.py.
- Each data type is processed concurrently, greatly improving speed.
- Progress callback is updated as each data type finishes.
- Error handling for individual data types is improved.
- Overall scalability and speed are significantly improved.

================================================================================
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..config import NOAA_BASE, NOAA_HEADERS, NOAA_TIDES_DEFAULT_DATUM, NOAA_TIDES_DEFAULT_TIMEZONE
from .utils import get_optimal_workers

def fetch_noaa_layers(progress_cb=None):
    layers = []
    errors = []
    data_types = ["alerts", "stations", "radar", "tides"]
    total = len(data_types)
    max_workers = min(get_optimal_workers(), total)  # Only 4 types

    def fetch_alerts():
        result = []
        try:
            resp = requests.get(f"{NOAA_BASE}/alerts/active", headers=NOAA_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                name = props.get("headline") or props.get("event") or "NOAA Alert"
                desc = props.get("description") or props.get("event") or ""
                url = props.get("uri") or props.get("id") or ""
                result.append({
                    "name": name,
                    "type": "NOAA Alert",
                    "endpoint": url,
                    "formats": "GeoJSON",
                    "properties": props,
                    "description": desc,
                    "url": url,
                    "series": "Active Alerts",
                    "source": "NOAA"
                })
        except Exception as e:
            errors.append(("alerts", str(e)))
            print(f"Error fetching NOAA alerts: {e}")
        return result

    def fetch_stations():
        result = []
        try:
            resp = requests.get(f"{NOAA_BASE}/stations", headers=NOAA_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                name = props.get("name") or props.get("stationIdentifier") or "NOAA Station"
                url = props.get("@id") or ""
                desc = props.get("name") or ""
                result.append({
                    "name": name,
                    "type": "NOAA Station",
                    "endpoint": url,
                    "formats": "GeoJSON",
                    "properties": props,
                    "description": desc,
                    "url": url,
                    "series": "Stations",
                    "source": "NOAA"
                })
        except Exception as e:
            errors.append(("stations", str(e)))
            print(f"Error fetching NOAA stations: {e}")
        return result

    def fetch_radar():
        result = []
        try:
            resp = requests.get(f"{NOAA_BASE}/radar/stations", headers=NOAA_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                name = props.get("name") or props.get("stationIdentifier") or "NOAA Radar"
                url = props.get("@id") or ""
                desc = props.get("name") or ""
                result.append({
                    "name": name,
                    "type": "NOAA Radar",
                    "endpoint": url,
                    "formats": "GeoJSON",
                    "properties": props,
                    "description": desc,
                    "url": url,
                    "series": "Radar Stations",
                    "source": "NOAA"
                })
        except Exception as e:
            errors.append(("radar", str(e)))
            print(f"Error fetching NOAA radar stations: {e}")
        return result

    def fetch_tides():
        result = []
        try:
            params = {
                "station": "9447130",
                "product": "water_level",
                "date": "today",
                "datum": NOAA_TIDES_DEFAULT_DATUM,
                "time_zone": NOAA_TIDES_DEFAULT_TIMEZONE,      
                "units": "metric",
                "format": "json"
            }
            resp = requests.get(
                "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
                params=params,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            for obs in data.get("data", []):
                name = f"NOAA Tides {obs.get('t','')}"
                desc = f"Water Level: {obs.get('v','')} {obs.get('s','')}"
                url = "https://tidesandcurrents.noaa.gov/"
                result.append({
                    "name": name,
                    "type": "NOAA Tides",
                    "endpoint": url,
                    "formats": "JSON",
                    "properties": obs,
                    "description": desc,
                    "url": url,
                    "series": "Tides",
                    "source": "NOAA"
                })
        except Exception as e:
            errors.append(("tides", str(e)))
            print(f"Error fetching NOAA tides: {e}")
        return result

    fetch_funcs = {
        "alerts": fetch_alerts,
        "stations": fetch_stations,
        "radar": fetch_radar,
        "tides": fetch_tides
    }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_funcs[dt]): dt for dt in data_types}
        for idx, future in enumerate(as_completed(futures)):
            dt = futures[future]
            result = future.result()
            layers.extend(result)
            if progress_cb:
                progress_cb(int(((idx+1)/total)*100), f"NOAA: {idx+1}/{total} data types")

    if errors:
        for dt, err in errors:
            print(f"Error fetching NOAA {dt}: {err}")
        if progress_cb:
            progress_cb(100, f"NOAA: Error(s) in {len(errors)} data type(s)")
    elif progress_cb:
        progress_cb(100, f"NOAA: {len(layers)} layers")
    return layers