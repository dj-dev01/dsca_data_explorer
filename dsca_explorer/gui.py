# dsca_explorer/gui.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import webbrowser
import concurrent.futures
import json

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

    def select_all(self):
    # Only select leaf nodes (not group nodes)
        if not hasattr(self, "group_nodes"):
            return
        for group_id in self.group_nodes.values():
            for child in self.tree.get_children(group_id):
                self.tree.selection_add(child)

    def clear_selection(self):
        self.tree.selection_remove(self.tree.get_children())

    def fetch_layers(self):
        self.status_var.set("Fetching layers...")
        self.progress["mode"] = "indeterminate"
        self.progress.start()
        self.progress_label.set("Fetching all sources in parallel...")
        threading.Thread(target=self._multifetch_layers_thread, daemon=True).start()

    def _multifetch_layers_thread(self):
        fetch_funcs = [
            fetch_arcgis_layers_all,
            fetch_openfema_layers,
            fetch_hifld_layers,
            fetch_noaa_layers,
            fetch_usgs_layers,
            fetch_epa_layers,
            fetch_nasa_layers,
        ]
        layers = []
        source_counts = {k: 0 for k in self.source_counts}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(fetch_funcs)) as executor:
            futures = [executor.submit(f) for f in fetch_funcs]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if isinstance(result, dict):  # For arcgis, which returns {'layers':..., 'count':...}
                    layers.extend(result['layers'])
                    source_counts['FEMA'] = result.get('count', 0)
                elif isinstance(result, list):
                    layers.extend(result)
        for src in ["OpenFEMA", "HIFLD", "NOAA", "USGS", "EPA", "NASA"]:
            source_counts[src] = len([l for l in layers if l.get("source") == src])
        new_layers, updated_layers = detect_new_or_updated_layers(layers)
        self.all_layers = layers
        self.source_counts = source_counts
        self.root.after(0, self._update_ui_after_fetch)
        if new_layers or updated_layers:
            msg = ""
            if new_layers:
                msg += f"New layers detected: {len(new_layers)}\n"
                msg += "\n".join(f"- {l['name']} ({l['source']})" for l in new_layers[:10])
                if len(new_layers) > 10:
                    msg += f"\n...and {len(new_layers)-10} more."
            if updated_layers:
                msg += f"\n\nUpdated layers detected: {len(updated_layers)}\n"
                msg += "\n".join(f"- {l['name']} ({l['source']})" for l in updated_layers[:10])
                if len(updated_layers) > 10:
                    msg += f"\n...and {len(updated_layers)-10} more."
            self.root.after(0, lambda: messagebox.showinfo("New/Updated Layers", msg))

    def _update_ui_after_fetch(self):
        total = sum(self.source_counts.values())
        self.counter_var.set(
            f"FEMA: {self.source_counts['FEMA']} | OpenFEMA: {self.source_counts['OpenFEMA']} | HIFLD: {self.source_counts['HIFLD']} | NOAA: {self.source_counts['NOAA']} | USGS: {self.source_counts['USGS']} | EPA: {self.source_counts['EPA']} | NASA: {self.source_counts['NASA']} | Total: {total}"
        )
        self.progress.stop()
        self.status_var.set(f"Found {total} layers")
        self.progress_label.set("")
        self.apply_filters()

    def apply_filters(self):
        endpoint = self.endpoint_var.get()
        fmt = self.format_var.get()
        typ = self.type_var.get()
        search = self.search_var.get().lower()
        self.filtered_layers = []
        for layer in self.all_layers:
            if endpoint != "All":
                if endpoint == "OpenFEMA" and layer["type"] != "OpenFEMA":
                    continue
                elif endpoint == "HIFLD" and layer["type"] != "HIFLD":
                    continue
                elif endpoint == "NOAA" and not layer["type"].startswith("NOAA"):
                    continue
                elif endpoint == "USGS" and not layer["type"].startswith("USGS"):
                    continue
                elif endpoint == "EPA" and not layer["type"].startswith("EPA"):
                    continue
                elif endpoint == "NASA" and not layer["type"].startswith("NASA"):
                    continue
                elif endpoint not in ["OpenFEMA", "HIFLD", "NOAA", "USGS", "EPA", "NASA"] and endpoint not in get_endpoint_name(str(layer["endpoint"])):
                    continue
            if fmt != "All" and fmt not in layer["formats"]:
                continue
            if typ != "All" and typ != layer["type"]:
                continue
            if search and search not in layer["name"].lower():
                continue
            self.filtered_layers.append(layer)
        self._populate_tree()

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        groups = {}
        for layer in self.filtered_layers:
            group = layer.get("series", "Other")
            if group not in groups:
                groups[group] = []
            groups[group].append(layer)
        self.group_nodes = {}
        for group in sorted(groups.keys()):
            group_label = f"{group} ({len(groups[group])})"
            group_id = self.tree.insert("", tk.END, text=group_label, values=("", "", "", ""))
            self.group_nodes[group] = group_id
            for layer in sorted(groups[group], key=lambda l: l["name"].lower()):
                self.tree.insert(group_id, tk.END, values=(
                    layer["name"], layer["type"], layer["endpoint"], layer["formats"]
                ))

    def show_layer_details(self, event=None):
        selected = self.tree.selection()
        if not selected:
            self.details_text.delete(1.0, tk.END)
            return
        item = self.tree.item(selected[0])
        values = item["values"]
        if not values or not values[0]:
            self.details_text.delete(1.0, tk.END)
            return
        layer = next((l for l in self.filtered_layers if l["name"] == values[0] and l["endpoint"] == values[2]), None)
        if not layer:
            self.details_text.delete(1.0, tk.END)
            return
        details = f"Name: {layer['name']}\nType: {layer['type']}\nEndpoint: {layer['endpoint']}\nFormats: {layer['formats']}\n"
        if layer.get("description"):
            details += f"\nDescription:\n{layer['description']}\n"
        if layer.get("dataDictionary"):
            details += f"\nData Dictionary: {layer['dataDictionary']}\n"
        if layer.get("landingPage"):
            details += f"\nLanding Page: {layer['landingPage']}\n"
        details += "\nAll Properties:\n"
        details += json.dumps(layer.get("properties", {}), indent=2)
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.details_text.tag_configure("url", foreground="blue", underline=True)
        for key in ["endpoint", "url", "dataDictionary", "landingPage"]:
            url = layer.get(key)
            if url and url.startswith("http"):
                idx = self.details_text.search(url, "1.0", tk.END)
                if idx:
                    end = f"{idx}+{len(url)}c"
                    self.details_text.tag_add("url", idx, end)
                    self.details_text.tag_bind("url", "<Button-1>", lambda e, url=url: webbrowser.open(url))

    def export_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Export", "No layers selected.")
            return
        layers = []
        for sel in selected:
            item = self.tree.item(sel)
            values = item["values"]
            if not values or not values[0]:
                continue
            layer = next((l for l in self.filtered_layers if l["name"] == values[0] and l["endpoint"] == values[2]), None)
            if layer:
                layers.append(layer)
        if not layers:
            messagebox.showinfo("Export", "No layers selected.")
            return

        formats = [("CSV", "*.csv"), ("Excel", "*.xlsx"), ("JSON", "*.json"), ("Text", "*.txt"), ("Word", "*.docx"), ("PDF", "*.pdf")]
        filetypes = formats
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=filetypes)
        if not file_path:
            return

        try:
            export_layers(layers, file_path)
            messagebox.showinfo("Export", f"Exported {len(layers)} layers to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def sort_by_column(self, col):
        self.sort_reverse = not self.sort_reverse
        self.filtered_layers.sort(key=lambda x: x.get(col, "").lower() if isinstance(x.get(col, ""), str) else str(x.get(col, "")), reverse=self.sort_reverse)
        self._populate_tree()

    def show_context_menu(self, event):
        rowid = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if rowid and col:
            self.tree.selection_set(rowid)
            self.context_menu.post(event.x_root, event.y_root)
            self._context_rowid = rowid
            self._context_col = int(col.replace("#", "")) - 1

    def copy_cell(self):
        item = self.tree.item(self._context_rowid)
        value = item["values"][self._context_col]
        self.root.clipboard_clear()
        self.root.clipboard_append(str(value))

    def copy_row(self):
        item = self.tree.item(self._context_rowid)
        values = item["values"]
        self.root.clipboard_clear()
        self.root.clipboard_append("\t".join(str(v) for v in values))

    def quick_filter(self, label):
        self.search_var.set(label.lower())
        self.apply_filters()
