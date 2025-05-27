"""
================================================================================
DSCA Explorer EPA Fetcher - Change Log
================================================================================

BEFORE:
-------
- Fetched EPA water system layers for a single state (CA) sequentially.
- Used a single HTTP request and processed results in a loop.
- No parallelization; slow if fetching multiple states or large datasets.

AFTER:
------
- Added parallel fetching of EPA water system layers for multiple states using
  ThreadPoolExecutor and get_optimal_workers() from utils.py.
- Now supports fetching multiple states in parallel (default is still CA).
- Progress callback updated as each state finishes.
- Errors for individual states are reported but do not halt the process.
- Improved scalability and speed for multi-state or large-scale data pulls.

================================================================================
"""


import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..config import EPA_BASE
from .utils import get_optimal_workers

def fetch_epa_layers(progress_cb=None, states=None):
    """
    Fetch EPA water system layers for multiple states in parallel.
    By default, fetches only California. Pass a list of state codes to fetch more.
    """
    if states is None:
        states = ["CA"]  # Default to California; add more state codes as needed

    layers = []
    errors = []
    max_workers = get_optimal_workers()

    def fetch_state(state):
        url = f"{EPA_BASE}/WATER_SYSTEM/STATE/{state}/ROWS/0:10/JSON"
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            state_layers = []
            for ws in data:
                name = ws.get("PWS_NAME") or "EPA Water System"
                desc = ws.get("PWS_ACTIVITY_CODE", "")
                endpoint_url = "https://enviro.epa.gov/"
                state_layers.append({
                    "name": name,
                    "type": "EPA Water System",
                    "endpoint": endpoint_url,
                    "formats": "JSON",
                    "properties": ws,
                    "description": desc,
                    "url": endpoint_url,
                    "series": "EPA Water",
                    "source": "EPA"
                })
            return state_layers
        except Exception as e:
            errors.append((state, str(e)))
            return []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_state, state): state for state in states}
        total = len(states)
        for idx, future in enumerate(as_completed(futures)):
            state = futures[future]
            state_layers = future.result()
            layers.extend(state_layers)
            if progress_cb:
                progress_cb(int(((idx+1)/total)*100), f"EPA: {idx+1}/{total} states")
    
    if errors:
        for state, err in errors:
            print(f"Error fetching EPA water systems for {state}: {err}")
        if progress_cb:
            progress_cb(100, f"EPA: Error(s) in {len(errors)} state(s)")
    elif progress_cb:
        progress_cb(100, f"EPA: {len(layers)} layers")

    return layers
