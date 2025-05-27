"""
================================================================================
DSCA Explorer ASH3D Fetcher - Change Log
================================================================================

NEW:
----
- Added fetch_ash3d_layers to pull latest USGS ASH3D volcano ashfall projections.
- Fetches recent public ASH3D runs and retrieves GeoJSON ashfall data for each.
- Returns layers compatible with the DSCA Explorer system.
- Ensures 'source' is 'USGS' and 'type' is 'ASH3D' for proper filtering.

================================================================================
"""

import requests


def fetch_ash3d_layers(progress_cb=None, limit=5):
    """
    Fetch latest USGS ASH3D volcano ashfall projections as GeoJSON layers.
    Returns a list of layer dicts.
    """
    layers = []
    try:
        if progress_cb:
            progress_cb(0, "Fetching latest ASH3D public runs")
        runs_url = "https://avo-vsc-ash.wr.usgs.gov/ash3d-api/publicApi/publicruns"
        resp = requests.get(runs_url, timeout=15)
        resp.raise_for_status()
        runs = resp.json()
        runs = runs[:limit]
        total = len(runs)
        for idx, run in enumerate(runs):
            job_cd = run.get("job_cd")
            run_type_cd = run.get("run_type_cd")
            volcano = run.get("volcano", "Unknown Volcano")
            eruption_time = run.get("eruption_time", "")
            if not job_cd or not run_type_cd:
                continue
            geojson_url = f"https://avo-vsc-ash.wr.usgs.gov/ash3d-api/mapApi/geojson/{job_cd}/{run_type_cd}?units=english"
            try:
                geojson_resp = requests.get(geojson_url, timeout=15)
                geojson_resp.raise_for_status()
                geojson = geojson_resp.json()
                layers.append({
                    "name": f"ASH3D {volcano} {eruption_time}",
                    "type": "ASH3D",  
                    "endpoint": geojson_url,
                    "formats": "GeoJSON",
                    "properties": geojson,
                    "description": f"USGS ASH3D ashfall projection for {volcano} at {eruption_time}",
                    "url": geojson_url,
                    "series": "ASH3D",
                    "source": "USGS"
                })
            except Exception as e:
                print(f"Error fetching ASH3D GeoJSON for {job_cd}/{run_type_cd}: {e}")
            if progress_cb:
                progress_cb(int(((idx+1)/total)*100), f"ASH3D: {idx+1}/{total} runs")
        if progress_cb:
            progress_cb(100, f"ASH3D: {len(layers)} layers")
    except Exception as e:
        print(f"Error fetching ASH3D public runs: {e}")
        if progress_cb:
            progress_cb(100, "ASH3D: Error")
    return layers
