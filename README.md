# DSCA Data Explorer

A modern Python tool for ingesting, viewing, and exporting geospatial layers from FEMA, USGS, NASA, EPA, HIFLD, ASH3D, and more.  
Features parallel fetching, robust change detection, dynamic GUI filtering, and multi-format export.

---

## Features

- **Parallel fetching** of all supported sources for fast data updates
- **Change detection** with field-level diffing and audit trail
- **Dynamic GUI** with source/format/type filters that update based on loaded data
- **Grouped change summary** popup per source
- **Export changes** or all layers in CSV, Excel, JSON, TXT, DOCX, or PDF
- **ASH3D volcano ashfall projections** integration
- **Modern, maintainable codebase** with clear separation of fetchers, cache, export, and GUI

---

## File Structure
```
dsca_data_explorer/
├── dsca_explorer/
│   ├── __init__.py
│   ├── gui.py
│   ├── cache.py
│   ├── export.py
│   ├── config.py
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── arcgis.py
│   │   ├── epa.py
│   │   ├── fema.py
│   │   ├── hifld.py
│   │   ├── nasa.py
│   │   ├── noaa.py
│   │   ├── usgs.py
│   │   ├── ash3d.py
│   │   └── utils.py
│   └── ...
├── run_explorer.py
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

---

## Installation

1. **Clone the repo:**
    ```sh
    git clone https://github.com/dj-dev01/dsca_data_explorer.git
    cd dsca_data_explorer
    ```

2. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

3. *(Optional but recommended)*  
   Set up a virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

---

## Usage

### GUI

```sh
python run_explorer.py
```

The GUI will open. Click "Fetch Layers" to load data.
Use the filters to explore.
Use "Export" or "Export Changes" to save data.


## To-Do
- Nested/cross-referenced filtering (e.g., selecting a source updates available formats/types)
- Fix and modernize volcano API integration
- Additional UI improvements and responsiveness

## License
MIT License

## Contributors
Just D.J. for now!

## Acknowledgments
FEMA, USGS, NASA, EPA, HIFLD, and the open-source geospatial community.
