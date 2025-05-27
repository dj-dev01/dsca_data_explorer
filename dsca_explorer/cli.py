"""
================================================================================
DSCA Explorer CLI
================================================================================

What this does:
---------------
- Fetches all current layers from all supported sources (ArcGIS, GeoJSON, WMS)
  using the fetch_all_layers() function from dsca_explorer.fetchers.
- Detects new and updated layers by comparing the current layers to the cached
  state using detect_new_or_updated_layers() from dsca_explorer.cache.
- Lists detected changes (with field-level details) in the terminal.
- Prompts the user to optionally export these changes in a chosen format
  (csv, xlsx, json, txt, docx, pdf) using export_changes() from dsca_explorer.export.
- Saves the exported change log to a timestamped file in the specified directory.

Where it pulls its information:
-------------------------------
- Layer data is pulled from all sources via dsca_explorer.fetchers.fetch_all_layers(),
  which aggregates results from ArcGIS, GeoJSON, and WMS fetchers.
- Change detection uses the cache file (dsca_layer_cache.json) managed by dsca_explorer.cache.
- Exported change logs are generated from the detected changes only (not all layers).

================================================================================
"""


import click
from pathlib import Path
from datetime import datetime
from dsca_explorer.cache import detect_new_or_updated_layers
from dsca_explorer.export import export_changes
from dsca_explorer.fetchers import fetch_all_layers

@click.command()
@click.option("--format", default=None, help="Export format: csv, xlsx, json, txt, docx, pdf")
@click.option("--output-dir", default=".", type=click.Path(), help="Directory to save the export file")
def main(format, output_dir):
    layers = fetch_all_layers()
    changes = detect_new_or_updated_layers(layers)
    if not changes:
        click.echo("No changes detected.")
        return
    click.echo(f"Detected {len(changes)} change(s):\n")
    for c in changes:
        click.echo(f"- [{c.change_type}] {c.layer_id} at {c.detection_time.isoformat()}")
        for field, (old, new) in c.changed_fields.items():
            click.echo(f"    {field}: {old} -> {new}")
    if click.confirm("\nWould you like to export these changes?", default=True):
        if not format:
            format = click.prompt(
                "Export format (csv, xlsx, json, txt, docx, pdf)", 
                type=click.Choice(["csv", "xlsx", "json", "txt", "docx", "pdf"]), 
                default="csv"
            )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir) / f"changes_{timestamp}.{format}"
        export_changes(changes, format, output_path)
        click.echo(f"\nExported {len(changes)} changes to {output_path}")
    else:
        click.echo("No export performed.")

if __name__ == "__main__":
    main()
