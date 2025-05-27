================================================================================
DSCA Explorer - Changelog v0.3.0 (2025-05-26)
================================================================================

**Performance & Fetching**
--------------------------
- All fetchers now use ThreadPoolExecutor for parallel network requests.
- Added get_optimal_workers() utility for hardware-aware thread pool sizing.
- fetch_all_layers() now runs all source fetchers in parallel.
- Added ASH3D fetcher for USGS volcano ashfall projections.

**Cache & Change Detection**
---------------------------
- Refactored detect_new_or_updated_layers to:
    - Return a single list of ChangeRecord objects.
    - Store full layer dicts in the cache, not just hashes.
    - Support robust field-level diffing, with defensive handling for legacy cache formats.
    - Include timestamps and changed field metadata in each change record.
- Added serialize_changes utility for export compatibility.

**Export System**
-----------------
- Added export_changes() function to export change records in multiple formats (CSV, XLSX, JSON, TXT, DOCX, PDF).
- CLI and GUI now support exporting detected changes, not just raw layers.

**GUI Improvements**
-------------------
- Refactored GUI to use new ChangeRecord API.
- Change summary popup now shows grouped counts per source, not full lists.
- Dynamic source counts and filter dropdowns only show actual ingested data.
- Removed default source list until layers are loaded.
- Added 'Export Changes' button to the GUI for easy export of detected changes.
- Improved error handling and popup formatting.

**Error Handling & Robustness**
------------------------------
- Improved error handling for fetchers and export.
- Added debug output for API failures.
- Provided user-friendly fallback messages for network/API errors.
- Added documentation and code comments for troubleshooting.

**To-Do / Next Steps**
----------------------
- Implement nested/cross-referenced filtering for filters (e.g., selecting a source should dynamically update available formats/types, and vice versa).
- Fix and modernize volcano API integration (replace deprecated endpoints, add ashfall projections, etc.).
- Additional UI updates for clarity, usability, and responsiveness.
- Continue to refine dynamic filter dropdowns and source counts.
- Consider further modularization and test coverage improvements.

================================================================================
