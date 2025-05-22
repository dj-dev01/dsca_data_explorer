# dsca_explorer/fetchers/usgs.py

import requests
from ..config import USGS_HANS_BASE, USGS_GEOJSON, USGS_EQ_BASE, USGS_WATER_BASE, HIFLD_HEADERS

def fetch_usgs_layers(progress_cb=None):
    layers = []
    total = 6
    step = 0

    # Earthquakes
    try:
        if progress_cb:
            progress_cb(int((step/total)*100), "Fetching USGS Earthquakes")
        url = f"{USGS_EQ_BASE}?format=geojson&starttime=2024-01-01&minmagnitude=5"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            name = props.get("place") or "USGS Earthquake"
            desc = f"M{props.get('mag','')} - {props.get('place','')}"
            url = props.get("url") or ""
            layers.append({
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
        print(f"Error fetching USGS earthquakes: {e}")
    step += 1

    # Water
    try:
        if progress_cb:
            progress_cb(int((step/total)*100), "Fetching USGS Water Data")
        url = f"{USGS_WATER_BASE}?sites=01646500&parameterCd=00060&format=json"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for ts in data.get("value", {}).get("timeSeries", []):
            props = ts.get("sourceInfo", {})
            name = props.get("siteName") or "USGS Water Site"
            desc = props.get("siteCode", [{}])[0].get("value", "")
            url = f"https://waterdata.usgs.gov/nwis/uv?site_no={desc}"
            layers.append({
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
        print(f"Error fetching USGS water data: {e}")
    step += 1

    # Elevated Volcanoes
    try:
        if progress_cb:
            progress_cb(int((step/total)*100), "Fetching USGS Elevated Volcanoes")
        resp = requests.get(f"{USGS_HANS_BASE}/volcano/getElevatedVolcanoes", headers=HIFLD_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for v in data:
            name = v.get("volcanoName") or v.get("volcCode") or "USGS Volcano"
            desc = f"Alert: {v.get('currentColorCode','')}, {v.get('alertLevel','')}"
            url = f"https://volcanoes.usgs.gov/volcanoes/{v.get('volcCode','')}"
            layers.append({
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
        print(f"Error fetching USGS elevated volcanoes: {e}")
    step += 1

    # CAP Alerts
    try:
        if progress_cb:
            progress_cb(int((step/total)*100), "Fetching USGS CAP Alerts")
        resp = requests.get(f"{USGS_HANS_BASE}/volcano/getCAPElevated", headers=HIFLD_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for v in data:
            name = v.get("volcanoName") or v.get("volcCode") or "USGS CAP Alert"
            desc = v.get("headline") or v.get("description") or ""
            url = v.get("capUrl") or ""
            layers.append({
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
        print(f"Error fetching USGS CAP alerts: {e}")
    step += 1

    # Monitored Volcanoes
    try:
        if progress_cb:
            progress_cb(int((step/total)*100), "Fetching USGS Monitored Volcanoes")
        resp = requests.get(f"{USGS_HANS_BASE}/volcano/getMonitoredVolcanoes", headers=HIFLD_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for v in data:
            name = v.get("volcanoName") or v.get("volcCode") or "USGS Monitored Volcano"
            desc = v.get("region") or ""
            url = f"https://volcanoes.usgs.gov/volcanoes/{v.get('volcCode','')}"
            layers.append({
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
        print(f"Error fetching USGS monitored volcanoes: {e}")
    step += 1

    # GeoJSON Elevated Volcanoes
    try:
        if progress_cb:
            progress_cb(int((step/total)*100), "Fetching USGS GeoJSON Volcanoes")
        resp = requests.get(USGS_GEOJSON, headers=HIFLD_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            name = props.get("volcanoName") or props.get("volcCode") or "USGS GeoJSON Volcano"
            desc = f"Alert: {props.get('currentColorCode','')}, {props.get('alertLevel','')}"
            url = f"https://volcanoes.usgs.gov/volcanoes/{props.get('volcCode','')}"
            layers.append({
                "name": name,
                "type": "USGS GeoJSON Volcano",
                "endpoint": url,
                "formats": "GeoJSON",
                "properties": props,
                "description": desc,
                "url": url,
                "series": "GeoJSON Elevated",
                "source": "USGS"
            })
    except Exception as e:
        print(f"Error fetching USGS GeoJSON volcanoes: {e}")
    if progress_cb:
        progress_cb(100, f"USGS: {len(layers)} layers")
    return layers
