"""
================================================================================
DSCA Explorer HIFLD Fetcher - Change Log
================================================================================

BEFORE:
-------
- fetch_hifld_layers fetched all HIFLD services sequentially.
- Each service was processed one after another, resulting in slow performance
  when many services are present.
- No parallelization for per-service fetching.

AFTER:
------
- fetch_hifld_layers now fetches HIFLD service details in parallel using
  ThreadPoolExecutor and get_optimal_workers() from utils.py.
- Each service is processed concurrently, greatly improving speed for many services.
- Progress callback is updated as each service finishes.
- Error handling for individual services is improved.
- Overall scalability and speed are significantly improved.

================================================================================
"""

import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..config import HIFLD_BASE_URL, HIFLD_HEADERS
from .utils import infer_category_from_service, get_optimal_workers

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_hifld_layers(progress_cb=None):
    layers = []
    errors = []
    try:
        response = requests.get(HIFLD_BASE_URL, verify=False, headers=HIFLD_HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            services = data.get('services', [])
            total = len(services)
            max_workers = get_optimal_workers()
            
            def fetch_service(service):
                service_name = service.get('name', 'Unknown')
                service_type = service.get('type', 'Unknown')
                rest_url = f"{HIFLD_BASE_URL.split('?')[0]}/{service_name}/{service_type}"
                service_layers = []
                try:
                    details = requests.get(f"{rest_url}?f=pjson", verify=False, headers=HIFLD_HEADERS, timeout=10).json()
                    for layer in details.get('layers', []):
                        layer_name = layer.get('name', 'Unknown Layer')
                        category = details.get('tags', ['Uncategorized'])[0] if 'tags' in details and details['tags'] else infer_category_from_service(rest_url)
                        service_layers.append({
                            'name': layer_name,
                            'type': 'HIFLD',
                            'endpoint': rest_url,
                            'formats': 'JSON',
                            'properties': layer,
                            'description': details.get('description', ''),
                            'url': f"{rest_url}/{layer.get('id', 0)}",
                            'series': category,
                            'source': 'HIFLD'
                        })
                except Exception as e:
                    errors.append((rest_url, str(e)))
                    print(f"Error fetching layers from {rest_url}: {str(e)}")
                return service_layers

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(fetch_service, service): idx for idx, service in enumerate(services)}
                for idx, future in enumerate(as_completed(futures)):
                    service_layers = future.result()
                    layers.extend(service_layers)
                    if progress_cb:
                        progress_cb(int(((idx+1)/total)*100), f"HIFLD: {idx+1}/{total} services")
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
