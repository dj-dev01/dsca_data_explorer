# dsca_explorer/fetchers/noaa.py

import requests
from ..config import NOAA_BASE, NOAA_HEADERS

def fetch_noaa_layers(progress_cb=None):
    layers = []
    total = 4
    step = 0

    # Alerts
    try:
        if progress_cb:
            progress_cb(int((step/total)*100), "Fetching NOAA Alerts")
        resp = requests.get(f"{NOAA_BASE}/alerts/active", headers=NOAA_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            name = props.get("headline") or props.get("event") or "NOAA Alert"
            desc = props.get("description") or props.get("event") or ""
            url = props.get("uri") or props.get("id") or ""
            layers.append({
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
        print(f"Error fetching NOAA alerts: {e}")
    step += 1

    # Stations
    try:
        if progress_cb:
            progress_cb(int((step/total)*100), "Fetching NOAA Stations")
        resp = requests.get(f"{NOAA_BASE}/stations", headers=NOAA_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            name = props.get("name") or props.get("stationIdentifier") or "NOAA Station"
            url = props.get("@id") or ""
            desc = props.get("name") or ""
            layers.append({
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
        print(f"Error fetching NOAA stations: {e}")
    step += 1

    # Radar
    try:
        if progress_cb:
            progress_cb(int((step/total)*100), "Fetching NOAA Radar Stations")
        resp = requests.get(f"{NOAA_BASE}/radar/stations", headers=NOAA_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            name = props.get("name") or props.get("stationIdentifier") or "NOAA Radar"
            url = props.get("@id") or ""
            desc = props.get("name") or ""
            layers.append({
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
        print(f"Error fetching NOAA radar stations: {e}")
    step += 1

    # Tides
    try:
        if progress_cb:
            progress_cb(int((step/total)*100), "Fetching NOAA Tides")
        url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?station=9447130&product=water_level&format=json"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for obs in data.get("data", []):
            name = f"NOAA Tides {obs.get('t','')}"
            desc = f"Water Level: {obs.get('v','')} {obs.get('s','')}"
            url = "https://tidesandcurrents.noaa.gov/"
            layers.append({
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
        print(f"Error fetching NOAA tides: {e}")
    if progress_cb:
        progress_cb(100, f"NOAA: {len(layers)} layers")
    return layers
