# dsca_explorer/fetchers/hifld.py

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from ..config import HIFLD_BASE_URL, HIFLD_HEADERS
from .utils import infer_category_from_service

def fetch_hifld_layers(progress_cb=None):
    layers = []
    try:
        response = requests.get(HIFLD_BASE_URL, verify=False, headers=HIFLD_HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            services = data.get('services', [])
            total = len(services)
            for idx, service in enumerate(services):
                if progress_cb:
                    progress_cb(int((idx/total)*100), f"Fetching {service.get('name', 'Unknown')}")
                service_name = service.get('name', 'Unknown')
                service_type = service.get('type', 'Unknown')
                rest_url = f"{HIFLD_BASE_URL.split('?')[0]}/{service_name}/{service_type}"
                try:
                    details = requests.get(f"{rest_url}?f=pjson", verify=False, headers=HIFLD_HEADERS, timeout=10).json()
                    for layer in details.get('layers', []):
                        layer_name = layer.get('name', 'Unknown Layer')
                        category = details.get('tags', ['Uncategorized'])[0] if 'tags' in details and details['tags'] else infer_category_from_service(rest_url)
                        layers.append({
                            'name': layer_name,
                            'type': 'HIFLD',
                            'endpoint': rest_url,
                            'formats': 'JSON',
                            'properties': layer,
                            'description': details.get('description', ''),
                            'url': f"{rest_url}/{layer.get('id', 0)}",
                            'series': category,
                            'source': 'HIFLD'  # Always set the source!
                        })
                except Exception as e:
                    print(f"Error fetching layers from {rest_url}: {str(e)}")
            if progress_cb:
                progress_cb(100, f"HIFLD: {len(layers)} layers")
        else:
            print(f"Failed to load HIFLD data. Status code: {response.status_code}")
            if progress_cb:
                progress_cb(100, "HIFLD: Error")
    except Exception as e:
        print(f"Error fetching HIFLD data: {e}")
        if progress_cb:
            progress_cb(100, "HIFLD: Error")
    return layers
