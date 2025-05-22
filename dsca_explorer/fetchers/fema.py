# dsca_explorer/fetchers/fema.py

import requests
from ..config import FEMA_ENDPOINTS, DOC_URLS
from .utils import get_series_prefix

def fetch_arcgis_layers_all(progress_cb=None):
    layers = []
    total = len(FEMA_ENDPOINTS)
    for idx, base_url in enumerate(FEMA_ENDPOINTS):
        if progress_cb:
            progress_cb(int((idx/total)*100), f"Fetching {base_url}")
        layers.extend(fetch_arcgis_layers(base_url))
    if progress_cb:
        progress_cb(100, "Done")
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
                        "series": get_series_prefix(lyr.get("name", ""))
                    })
            except Exception as e:
                continue
    except Exception as e:
        print(f"Error fetching ArcGIS layers from {base_url}: {e}")
    return layers

def fetch_openfema_layers():
    layers = []
    try:
        url = "https://www.fema.gov/api/open/v1/DataSets"
        res = requests.get(url, timeout=20)
        res.raise_for_status()
        datasets = res.json().get("DataSets", [])
        for ds in datasets:
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
                "series": series
            })
    except Exception as e:
        print(f"Error fetching OpenFEMA layers: {e}")
    return layers
