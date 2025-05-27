from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def fetch_usgs_layers(progress_cb=None):
    """
    Fetches USGS layers: earthquakes, water data, and volcanoes (all, monitored, elevated, CAP-elevated).
    Returns a list of layer dictionaries.
    """
    layers = []
    errors = []
    data_types = [
        "earthquakes",
        "water",
        "us_volcanoes",
        "monitored_volcanoes",
        "elevated_volcanoes",
        "cap_elevated_volcanoes"
    ]
    total = len(data_types)
    max_workers = min(6, total)

    # Endpoints
    USGS_EQ_BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    USGS_WATER_BASE = "https://waterservices.usgs.gov/nwis/iv/"
    USGS_VOLCANOES_BASE = "https://volcanoes.usgs.gov/hans-public/api/volcano"

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
                eq_url = props.get("url") or ""
                result.append({
                    "name": name,
                    "type": "USGS Earthquake",
                    "endpoint": eq_url,
                    "formats": "GeoJSON",
                    "properties": props,
                    "description": desc,
                    "url": eq_url,
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
                site_url = f"https://waterdata.usgs.gov/nwis/uv?site_no={desc}"
                result.append({
                    "name": name,
                    "type": "USGS Water Site",
                    "endpoint": site_url,
                    "formats": "JSON",
                    "properties": props,
                    "description": desc,
                    "url": site_url,
                    "series": "Water Data",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("water", str(e)))
            print(f"Error fetching USGS water data: {e}")
        return result

    def fetch_us_volcanoes():
        result = []
        try:
            url = f"{USGS_VOLCANOES_BASE}/getUSVolcanoes"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for volcano in data:
                name = volcano.get("volcanoName") or volcano.get("volcanoID") or "USGS Volcano"
                code = volcano.get("volcanoID", "")
                region = volcano.get("region", "")
                alert = volcano.get("alertLevel", "")
                color = volcano.get("currentColorCode", "")
                desc = f"Region: {region} | Alert: {alert} | Color: {color}"
                volcano_url = f"https://volcanoes.usgs.gov/volcanoes/{code}" if code else "https://volcanoes.usgs.gov/"
                result.append({
                    "name": name,
                    "type": "USGS Volcano",
                    "endpoint": volcano_url,
                    "formats": "JSON",
                    "properties": volcano,
                    "description": desc,
                    "url": volcano_url,
                    "series": "US Volcanoes",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("us_volcanoes", str(e)))
            print(f"Error fetching USGS US volcanoes: {e}")
        return result

    def fetch_monitored_volcanoes():
        result = []
        try:
            url = f"{USGS_VOLCANOES_BASE}/getMonitoredVolcanoes"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for volcano in data:
                name = volcano.get("volcanoName") or volcano.get("volcanoID") or "USGS Monitored Volcano"
                code = volcano.get("volcanoID", "")
                region = volcano.get("region", "")
                alert = volcano.get("alertLevel", "")
                color = volcano.get("currentColorCode", "")
                desc = f"Region: {region} | Alert: {alert} | Color: {color}"
                volcano_url = f"https://volcanoes.usgs.gov/volcanoes/{code}" if code else "https://volcanoes.usgs.gov/"
                result.append({
                    "name": name,
                    "type": "USGS Monitored Volcano",
                    "endpoint": volcano_url,
                    "formats": "JSON",
                    "properties": volcano,
                    "description": desc,
                    "url": volcano_url,
                    "series": "Monitored Volcanoes",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("monitored_volcanoes", str(e)))
            print(f"Error fetching USGS monitored volcanoes: {e}")
        return result

    def fetch_elevated_volcanoes():
        result = []
        try:
            url = f"{USGS_VOLCANOES_BASE}/getElevatedVolcanoes"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for volcano in data:
                name = volcano.get("volcanoName") or volcano.get("volcanoID") or "USGS Elevated Volcano"
                code = volcano.get("volcanoID", "")
                region = volcano.get("region", "")
                alert = volcano.get("alertLevel", "")
                color = volcano.get("currentColorCode", "")
                desc = f"Region: {region} | Alert: {alert} | Color: {color}"
                volcano_url = f"https://volcanoes.usgs.gov/volcanoes/{code}" if code else "https://volcanoes.usgs.gov/"
                result.append({
                    "name": name,
                    "type": "USGS Elevated Volcano",
                    "endpoint": volcano_url,
                    "formats": "JSON",
                    "properties": volcano,
                    "description": desc,
                    "url": volcano_url,
                    "series": "Elevated Volcanoes",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("elevated_volcanoes", str(e)))
            print(f"Error fetching USGS elevated volcanoes: {e}")
        return result

    def fetch_cap_elevated_volcanoes():
        result = []
        try:
            url = f"{USGS_VOLCANOES_BASE}/getCapElevated"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for volcano in data:
                name = volcano.get("volcanoName") or volcano.get("volcanoID") or "USGS CAP-Elevated Volcano"
                code = volcano.get("volcanoID", "")
                region = volcano.get("region", "")
                alert = volcano.get("alertLevel", "")
                color = volcano.get("currentColorCode", "")
                desc = f"Region: {region} | Alert: {alert} | Color: {color}"
                volcano_url = f"https://volcanoes.usgs.gov/volcanoes/{code}" if code else "https://volcanoes.usgs.gov/"
                result.append({
                    "name": name,
                    "type": "USGS CAP-Elevated Volcano",
                    "endpoint": volcano_url,
                    "formats": "JSON",
                    "properties": volcano,
                    "description": desc,
                    "url": volcano_url,
                    "series": "CAP-Elevated Volcanoes",
                    "source": "USGS"
                })
        except Exception as e:
            errors.append(("cap_elevated_volcanoes", str(e)))
            print(f"Error fetching USGS CAP-elevated volcanoes: {e}")
        return result

    fetch_funcs = {
        "earthquakes": fetch_earthquakes,
        "water": fetch_water,
        "us_volcanoes": fetch_us_volcanoes,
        "monitored_volcanoes": fetch_monitored_volcanoes,
        "elevated_volcanoes": fetch_elevated_volcanoes,
        "cap_elevated_volcanoes": fetch_cap_elevated_volcanoes,
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
