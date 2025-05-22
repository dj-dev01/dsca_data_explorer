# dsca_explorer/cache.py

import json
import os
from .fetchers.utils import layer_hash

CACHE_FILE = "dsca_layer_cache.json"

def detect_new_or_updated_layers(layers):
    """
    Compare current layers to the last cache.
    Returns (new_layers, updated_layers).
    """
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
        except Exception:
            cache = {}
    new_layers = []
    updated_layers = []
    new_cache = {}
    for l in layers:
        key = f"{l.get('source','')}|{l.get('endpoint','')}|{l.get('name','')}"
        h = layer_hash(l)
        new_cache[key] = h
        if key not in cache:
            new_layers.append(l)
        elif cache[key] != h:
            updated_layers.append(l)
    with open(CACHE_FILE, "w") as f:
        json.dump(new_cache, f, indent=2)
    return new_layers, updated_layers
