# dsca_explorer/gui.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import webbrowser

from .config import DOC_URLS
from .fetchers import (
    fetch_arcgis_layers_all, fetch_openfema_layers, fetch_hifld_layers,
    fetch_noaa_layers, fetch_usgs_layers, fetch_epa_layers, fetch_nasa_layers,
    get_endpoint_name
)
from .export import export_layers
from .cache import detect_new_or_updated_layers

def run_gui():
    root = tk.Tk()
    app = DSCARestAPIExplorer(root)
    root.mainloop()

class DSCARestAPIExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("DSCA Data Explorer")
        self.root.geometry("1450x1100")
        self.all_layers = []
        self.filtered_layers = []
        self.sort_reverse = False
        self.source_counts = {
            "FEMA": 0, "OpenFEMA": 0, "HIFLD": 0, "NOAA": 0, "USGS": 0, "EPA": 0, "NASA": 0
        }
        self.create_widgets()

    def create_widgets(self):
        main_container = ttk.Frame(self.root, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)

        self.counter_var = tk.StringVar(value="FEMA: 0 | OpenFEMA: 0 | HIFLD: 0 | NOAA: 0 | USGS: 0 | EPA: 0 | NASA: 0 | Total: 0")
        counter_label = ttk.Label(main_container, textvariable=self.counter_var, font=("Arial", 11, "bold"))
        counter_label.pack(anchor=tk.W, pady=(0, 5))

        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="DSCA Data Explorer", font=("Arial", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text="Explore and export FEMA, HIFLD, OpenFEMA, NOAA, USGS, EPA, NASA REST API layers", font=("Arial", 10)).pack(anchor=tk.W)

        paned_window = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(paned_window, padding=5)
        bottom_frame = ttk.LabelFrame(paned_window, text="Layer Details", padding=5)
        paned_window.add(top_frame, weight=2)
        paned_window.add(bottom_frame, weight=1)

        control_frame = ttk.Frame(top_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        status_frame = ttk.Frame(control_frame)
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, mode="indeterminate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.progress_label = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.progress_label, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Fetch Layers", command=self.fetch_layers).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear", command=self.clear_selection).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Export", command=self.export_selected).pack(side=tk.LEFT, padx=2)

        filter_frame = ttk.LabelFrame(top_frame, text="Filters", padding=5)
        filter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filter_frame, text="Source:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.endpoint_var = tk.StringVar(value="All")
        self.endpoint_combo = ttk.Combobox(filter_frame, textvariable=self.endpoint_var, state="readonly")
        self.endpoint_combo.grid(row=0, column=1, padx=2, sticky=tk.EW)
        self.endpoint_combo['values'] = [
            "All"
        ] + [get_endpoint_name(url) for url in [
            "https://gis.fema.gov/arcgis/rest/services/FEMA",
            "https://hazards.fema.gov/arcgis/rest/services",
            "https://hazards.fema.gov/arcgis/rest/services/public/NFHL"
        ]] + [
            "OpenFEMA", "HIFLD", "NOAA", "USGS", "EPA", "NASA"
        ]
        self.endpoint_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        ttk.Label(filter_frame, text="Format:").grid(row=0, column=2, padx=2, sticky=tk.W)
        self.format_var = tk.StringVar(value="All")
        format_combo = ttk.Combobox(filter_frame, textvariable=self.format_var, 
                                  values=["All", "JSON", "CSV", "XLSX", "TXT", "DOCX", "PDF", "GeoJSON", "Parquet"], state="readonly")
        format_combo.grid(row=0, column=3, padx=2, sticky=tk.EW)
        format_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        ttk.Label(filter_frame, text="Type:").grid(row=0, column=4, padx=2, sticky=tk.W)
        self.type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(filter_frame, textvariable=self.type_var,
                                values=["All", "MapServer", "FeatureServer", "OpenFEMA", "HIFLD", "NOAA Alert", "NOAA Station", "NOAA Radar", "NOAA Tides", "USGS Earthquake", "USGS Water Site", "USGS Elevated Volcano", "USGS CAP Alert", "USGS Monitored Volcano", "USGS Notice", "USGS VONA", "USGS GeoJSON Volcano", "EPA Water System", "NASA Earthdata"], state="readonly")
        type_combo.grid(row=0, column=5, padx=2, sticky=tk.EW)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        ttk.Label(filter_frame, text="Search:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        search_entry.grid(row=1, column=1, columnspan=5, padx=2, sticky=tk.EW)
        search_entry.bind("<KeyRelease>", lambda e: self.apply_filters())

        tree_frame = ttk.Frame(top_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("name", "type", "endpoint", "formats")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", selectmode="extended")
        col_settings = [
            ("Layer Name", 400),
            ("Type", 100),
            ("Endpoint", 500),
            ("Formats", 100)
        ]
        for idx, (col, (heading, width)) in enumerate(zip(columns, col_settings)):
            self.tree.heading(col, text=heading, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=width, minwidth=width//2)

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.show_layer_details)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.details_text = scrolledtext.ScrolledText(bottom_frame, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy Cell", command=self.copy_cell)
        self.context_menu.add_command(label="Copy Row", command=self.copy_row)

    # All the methods from the previous monolithic version go here:
    # fetch_layers, _multifetch_layers_thread, _update_ui_after_fetch, apply_filters, _populate_tree,
    # show_layer_details, export_selected, sort_by_column, show_context_menu, copy_cell, copy_row, quick_filter, etc.
    # Each should call the appropriate fetchers from the fetchers package and use export_layers for export.

    # For brevity, refer to your previous code for these methods, but now import fetchers/export/cache as above.

