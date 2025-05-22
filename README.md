# DSCA Data Explorer

**DSCA Data Explorer** is a powerful, open-source Python application for discovering, monitoring, and exporting geospatial and environmental datasets from major U.S. government sources.  
It is designed for DSCA (Defense Support of Civil Authorities), emergency management, and research workflows.

- **Parallel multi-source fetch:** Pulls from FEMA, HIFLD, OpenFEMA, NOAA, USGS, EPA, and NASA at once.
- **Change detection:** Notifies you of new or updated layers since your last run.
- **Modern GUI:** Filter, search, and export with ease.
- **Export:** CSV, XLSX, JSON, TXT, DOCX, PDF.

**Ideal for:**  
- Emergency managers  
- GIS professionals  
- Researchers  
- Developers integrating federal data into their own tools
=======
A comprehensive, open-source Python GUI for discovering, monitoring, and exporting geospatial and environmental datasets from FEMA, HIFLD, OpenFEMA, NOAA, USGS, EPA, and NASA APIs.

## Features

- **Parallel multi-source fetch:** All sources are fetched at once for speed.
- **Layer change detection:** Notifies you of new or updated layers since your last run.
- **Powerful filtering:** By source, type, format, and search.
- **Export:** CSV, XLSX, JSON, TXT, DOCX, PDF.
- **Layer details:** View all properties, documentation links, and direct endpoints.
- **Copy/cell/row context menu:** For easy copy-paste.
- **Modern Tkinter GUI:** Responsive, with progress bar and counters.

## Supported Sources

- FEMA ArcGIS REST
- OpenFEMA
- HIFLD ArcGIS REST
- NOAA (alerts, stations, radar, tides)
- USGS (earthquakes, water, volcanoes/ashfall)
- EPA Envirofacts
- NASA Earthdata

## Installation

1. **Clone the repo:**
    ```bash
    git clone https://github.com/yourusername/dsca-data-explorer.git
    cd dsca-data-explorer
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the app:**
    ```bash
    python run_explorer.py
    ```

## Usage

- Click **Fetch Layers** to pull all sources in parallel.
- Filter by source, type, format, or search.
- Select layers and click **Export** to save as CSV, XLSX, JSON, TXT, DOCX, or PDF.
- On each fetch, you'll be notified of any new or updated layers since your last run.

## File Structure

dsca-data-explorer/
├── dsca_explorer/
│   ├── gui.py
│   ├── fetchers/
│   ├── export.py
│   ├── cache.py
│   ├── config.py
│   └── ...
├── requirements.txt
├── README.md
├── LICENSE
├── run_explorer.py
└── dsca_layer_cache.json    # (auto-generated) cache for change detection

## License

MIT License

## Acknowledgments

- FEMA, HIFLD, NOAA, USGS, EPA, NASA for open APIs and data.