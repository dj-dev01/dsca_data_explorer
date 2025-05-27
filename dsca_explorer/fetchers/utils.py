"""
================================================================================
DSCA Explorer Fetchers Utils - Change Log
================================================================================

BEFORE:
-------
- Provided utility functions for:
    - Hashing layers for change detection (layer_hash)
    - Inferring series prefix from layer names (get_series_prefix)
    - Inferring category from service URLs (infer_category_from_service)
    - Extracting endpoint names from URLs (get_endpoint_name)

AFTER:
------
- Added get_optimal_workers(multiplier=5, minimum=8, maximum=32):
    - Dynamically determines the optimal number of worker threads for
      ThreadPoolExecutor based on machine hardware (CPU count).
    - Enables automatic, efficient parallelization of network-bound fetchers.
- All other utility functions retained for hashing, categorization, and parsing.

================================================================================
"""


import hashlib
import json
import os
from urllib.parse import urlparse

def get_optimal_workers(multiplier=5, minimum=8, maximum=32):
    """
    Returns an optimal number of workers for ThreadPoolExecutor.
    For network-bound tasks, a higher multiplier is safe.
    """
    cpu_count = os.cpu_count() or 4
    return max(minimum, min(cpu_count * multiplier, maximum))

def get_series_prefix(name):
    if not name:
        return "Other"
    parts = name.split('-')
    if len(parts) > 1 and parts[0].isalpha():
        return parts[0]
    return "Other"

def infer_category_from_service(service_url):
    service_url = service_url.lower()
    if 'cell' in service_url:
        return 'Cell Towers'
    if 'power' in service_url or 'electric' in service_url:
        return 'Power/Electric'
    if 'border' in service_url or 'boundary' in service_url:
        return 'Borders' if 'border' in service_url else 'Boundaries'
    elif 'health' in service_url or 'hospital' in service_url:
        return 'Health'
    elif 'transport' in service_url or 'road' in service_url:
        return 'Transportation'
    elif 'energy' in service_url or 'power' in service_url:
        return 'Energy'
    elif 'emergency' in service_url or 'police' in service_url:
        return 'Emergency Services'
    else:
        return 'Uncategorized'

def layer_hash(layer):
    # Unique hash for a layer based on endpoint+name+type+properties
    h = hashlib.sha256()
    h.update((layer.get("endpoint","") + "|" + layer.get("name","") + "|" + layer.get("type","")).encode())
    h.update(json.dumps(layer.get("properties",{}), sort_keys=True).encode())
    return h.hexdigest()

def get_endpoint_name(url):
    parsed = urlparse(url)
    return f"{parsed.path.split('/')[-1]} ({parsed.netloc})"
