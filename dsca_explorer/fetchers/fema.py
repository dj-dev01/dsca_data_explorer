"""
================================================================================
DSCA Explorer FEMA Fetcher - Change Log
================================================================================

UPDATED:
--------
- Standardized 'source' field for both FEMA ArcGIS and OpenFEMA layers to "FEMA".
- Now "OpenFEMA" and "FEMA ArcGIS" are distinguished by the 'type' or 'series' field.
- Filtering and source counts will now combine all FEMA-related layers under "FEMA".

================================================================================
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from ..config import DOC_URLS, FEMA_ENDPOINTS, OPENFEMA_API
from .utils import get_optimal_workers, get_series_prefix


def fetch_arcgis_layers_all(progress_cb=None):
    layers = []
    errors = []
    total = len(FEMA_ENDPOINTS)
    max_workers = get_optimal_workers()

    def fetch_and_process(base_url):
        arc_layers = fetch_arcgis_layers(base_url)
        for l in arc_layers:
            l["source"] = "FEMA"  # Standardized
            l["documentation"] = DOC_URLS.get(l["type"], DOC_URLS["MapServer"])
            l["download_url"] = l.get("endpoint", "")
        return arc_layers

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_and_process, base_url): base_url for base_url in FEMA_ENDPOINTS}
        for idx, future in enumerate(as_completed(futures)):
            base_url = futures[future]
            try:
                arc_layers = future.result()
                layers.extend(arc_layers)
            except Exception as e:
                errors.append((base_url, str(e)))
            if progress_cb:
                progress_cb(int(((idx+1)/total)*100), f"FEMA: {idx+1}/{total} endpoints")

    if errors:
        for base_url, err in errors:
            print(f"Error fetching ArcGIS layers from {base_url}: {err}")
        if progress_cb:
            progress_cb(100, f"FEMA: Error(s) in {len(errors)} endpoint(s)")
    elif progress_cb:
        progress_cb(100, f"FEMA: {len(layers)} layers")
    return {'layers': layers, 'count': len(layers)}

def fetch_arcgis_layers(base_url):
    layers = []
    try:
        res = requests.get(f"{base_url}?f=json", timeout=15)
        res.raise_for_status()
        data = res.json()
        services = data.get("services", [])
        for svc in services:
            svc_name = svc.get("name")
            svc_type = svc.get("type")
            if not svc_name or not svc_type:
                continue
            if svc_type not in ["MapServer", "FeatureServer"]:
                continue
            svc_url = f"{base_url}/{svc_name.split('/')[-1]}/{svc_type}"
            try:
                svc_res = requests.get(f"{svc_url}?f=json", timeout=10)
                svc_res.raise_for_status()
                svc_data = svc_res.json()
                for lyr in svc_data.get("layers", []):
                    desc = lyr.get("description") or svc_data.get("serviceDescription") or ""
                    layers.append({
                        "name": lyr.get("name", "Unnamed"),
                        "type": svc_type,  # "MapServer" or "FeatureServer"
                        "endpoint": svc_url,
                        "formats": "JSON",
                        "properties": lyr,
                        "description": desc,
                        "url": f"{svc_url}/{lyr.get('id', 0)}",
                        "series": get_series_prefix(lyr.get("name", "")),
                        "source": "FEMA"  # Standardized
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"Error fetching ArcGIS layers from {base_url}: {e}")
    return layers

def fetch_openfema_layers(progress_cb=None):
    layers = []
    try:
        if progress_cb:
            progress_cb(0, "Fetching OpenFEMA datasets")
        url = OPENFEMA_API
        res = requests.get(url, timeout=20)
        res.raise_for_status()
        datasets = res.json().get("DataSets", [])
        total = len(datasets)
        for idx, ds in enumerate(datasets):
            endpoint = ds.get("apiEndpoint") or ds.get("accessURL") or ""
            name = ds.get("title") or ds.get("name") or "OpenFEMA Dataset"
            fmt = ds.get("format") or "JSON"
            desc = ds.get("description") or ""
            data_dict = ds.get("dataDictionary") or ""
            landing = ds.get("landingPage") or ""
            series = ds.get("theme") or ds.get("category") or "OpenFEMA"
            layers.append({
                "name": name,
                "type": "OpenFEMA",  # Distinguish by type
                "endpoint": endpoint,
                "formats": fmt,
                "properties": ds,
                "description": desc,
                "url": endpoint,
                "dataDictionary": data_dict,
                "landingPage": landing,
                "series": series,
                "source": "FEMA"  # Standardized
            })
            if progress_cb and total > 0:
                progress_cb(int(((idx+1)/total)*100), f"OpenFEMA: {idx+1}/{total}")
        if progress_cb:
            progress_cb(100, f"OpenFEMA: {len(layers)} layers")
    except Exception as e:
        print(f"Error fetching OpenFEMA layers: {e}")
        if progress_cb:
            progress_cb(100, "OpenFEMA: Error")
    return layers
