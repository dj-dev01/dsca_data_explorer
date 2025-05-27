"""
================================================================================
DSCA Explorer Fetchers Package - Change Log
================================================================================

UPDATED:
--------
- Added ASH3D fetcher (fetch_ash3d_layers) for USGS volcano ashfall projections.
- Now imports and exposes fetch_ash3d_layers.
- fetch_all_layers and GUI/CLI fetch lists now include ASH3D.

================================================================================
"""

from .fema import fetch_arcgis_layers_all, fetch_arcgis_layers, fetch_openfema_layers
from .hifld import fetch_hifld_layers
from .noaa import fetch_noaa_layers
from .usgs import fetch_usgs_layers
from .epa import fetch_epa_layers
from .nasa import fetch_nasa_layers
from .ash3d import fetch_ash3d_layers  # <-- NEW

from .utils import (
    get_series_prefix,
    infer_category_from_service,
    layer_hash,
    get_endpoint_name,
    get_optimal_workers
)

def fetch_all_layers(progress_cb=None):
    """
    Fetch all layers from all sources in parallel.
    Returns a combined list of all layers.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    fetchers = [
        fetch_arcgis_layers_all,
        fetch_openfema_layers,
        fetch_hifld_layers,
        fetch_noaa_layers,
        fetch_usgs_layers,
        fetch_epa_layers,
        fetch_nasa_layers,
        fetch_ash3d_layers,  # <-- NEW
    ]
    names = [
        "FEMA ArcGIS",
        "OpenFEMA",
        "HIFLD",
        "NOAA",
        "USGS",
        "EPA",
        "NASA",
        "ASH3D",  # <-- NEW
    ]
    max_workers = min(get_optimal_workers(), len(fetchers))
    all_layers = []
    errors = []

    def run_fetcher(fetcher, name):
        try:
            result = fetcher(progress_cb)
            if isinstance(result, dict) and "layers" in result:
                return result["layers"]
            return result
        except Exception as e:
            errors.append((name, str(e)))
            print(f"Error in {name}: {e}")
            return []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_fetcher, fetcher, name): name for fetcher, name in zip(fetchers, names)}
        for future in as_completed(futures):
            layers = future.result()
            all_layers.extend(layers)

    if errors:
        for name, err in errors:
            print(f"Error in {name}: {err}")

    return all_layers
