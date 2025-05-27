"""
================================================================================
DSCA Explorer FEMA Fetcher - Change Log
================================================================================

BEFORE:
-------
- fetch_arcgis_layers_all fetched ArcGIS layers from FEMA_ENDPOINTS sequentially.
- Each endpoint was processed one after another, resulting in slow performance
  when many endpoints are present.
- fetch_openfema_layers fetched OpenFEMA datasets in a single request (no change).
- No parallelization for ArcGIS endpoint fetching.

AFTER:
------
- fetch_arcgis_layers_all now fetches ArcGIS layers from all FEMA_ENDPOINTS in
  parallel using ThreadPoolExecutor and get_optimal_workers() from utils.py.
- Each endpoint is processed concurrently, greatly improving speed for multiple endpoints.
- Progress callback is updated as each endpoint finishes.
- Error handling for individual endpoints is improved.
- fetch_openfema_layers remains unchanged (single API call, not parallelizable).

================================================================================
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..config import FEMA_ENDPOINTS, DOC_URLS, OPENFEMA_API
from .utils import get_series_prefix, get_optimal_workers

def fetch_arcgis_layers_all(progress_cb=None):
    layers = []
    errors = []
    total = len(FEMA_ENDPOINTS)
    max_workers = get_optimal_workers()

    def fetch_and_process(base_url):
        arc_layers = fetch_arcgis_layers(base_url)
        for l in arc_layers:
            l["source"] = "FEMA"
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
                        "type": svc_type,
                        "endpoint": svc_url,
                        "formats": "JSON",
                        "properties": lyr,
                        "description": desc,
                        "url": f"{svc_url}/{lyr.get('id', 0)}",
                        "series": get_series_prefix(lyr.get("name", "")),
                        "source": "FEMA"
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
                "type": "OpenFEMA",
                "endpoint": endpoint,
                "formats": fmt,
                "properties": ds,
                "description": desc,
                "url": endpoint,
                "dataDictionary": data_dict,
                "landingPage": landing,
                "series": series,
                "source": "OpenFEMA"
            })
            if progress_cb and total > 0:
                progress_cb(int((idx/total)*100), f"OpenFEMA: {idx+1}/{total}")
        if progress_cb:
            progress_cb(100, f"OpenFEMA: {len(layers)} layers")
    except Exception as e:
        print(f"Error fetching OpenFEMA layers: {e}")
        if progress_cb:
            progress_cb(100, "OpenFEMA: Error")
    return layers
