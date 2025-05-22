# dsca_explorer/fetchers/utils.py

import hashlib
import json
from urllib.parse import urlparse

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
