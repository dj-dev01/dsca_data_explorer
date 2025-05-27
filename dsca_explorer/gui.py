import concurrent.futures
import json
import threading
import tkinter as tk
import webbrowser
from collections import defaultdict
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .cache import detect_new_or_updated_layers
from .config import DOC_URLS
from .export import export_layers
from .fetchers import (fetch_arcgis_layers_all, fetch_ash3d_layers,
                       fetch_epa_layers, fetch_hifld_layers, fetch_nasa_layers,
                       fetch_noaa_layers, fetch_openfema_layers,
                       fetch_usgs_layers, get_endpoint_name)


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
        self.source_counts = {}
        self.last_changes = []
        self.create_widgets()

    def create_widgets(self):
        main_container = ttk.Frame(self.root, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)

        self.counter_var = tk.StringVar(value="No layers loaded yet!")
        counter_label = ttk.Label(main_container, textvariable=self.counter_var, font=("Arial", 11, "bold"))
        counter_label.pack(anchor=tk.W, pady=(0, 5))

        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="DSCA Data Explorer", font=("Arial", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(header_frame, text="A tool for exploring, viewing, and exporting DSCA geospatial layers.", font=("Arial", 10)).pack(anchor=tk.W)

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
        self.progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, mode="determinate", maximum=100)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.progress_label = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.progress_label, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Fetch Layers", command=self.fetch_layers).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear", command=self.clear_selection).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Export", command=self.export_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Export Changes", command=self.export_changes).pack(side=tk.LEFT, padx=2)

        filter_frame = ttk.LabelFrame(top_frame, text="Filters", padding=5)
        filter_frame.pack(fill=tk.X, pady=5)

        # Source filter
        ttk.Label(filter_frame, text="Source:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.endpoint_var = tk.StringVar(value="All")
        self.endpoint_combo = ttk.Combobox(filter_frame, textvariable=self.endpoint_var, values=["All"], state="readonly")
        self.endpoint_combo.grid(row=0, column=1, padx=2, sticky=tk.EW)
        self.endpoint_combo.bind("<<ComboboxSelected>>", lambda e: self.update_filter_options())

        # Format filter
        ttk.Label(filter_frame, text="Format:").grid(row=0, column=2, padx=2, sticky=tk.W)
        self.format_var = tk.StringVar(value="All")
        self.format_combo = ttk.Combobox(filter_frame, textvariable=self.format_var, values=["All"], state="readonly")
        self.format_combo.grid(row=0, column=3, padx=2, sticky=tk.EW)
        self.format_combo.bind("<<ComboboxSelected>>", lambda e: self.update_filter_options())

        # Type filter
        ttk.Label(filter_frame, text="Type:").grid(row=0, column=4, padx=2, sticky=tk.W)
        self.type_var = tk.StringVar(value="All")
        self.type_combo = ttk.Combobox(filter_frame, textvariable=self.type_var, values=["All"], state="readonly")
        self.type_combo.grid(row=0, column=5, padx=2, sticky=tk.EW)
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self.update_filter_options())

        # Search filter
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

    def update_filter_options(self):
        selected_source = self.endpoint_var.get()
        selected_format = self.format_var.get()
        selected_type = self.type_var.get()

        # Source options: all sources present in layers matching current format and type
        source_layers = self.all_layers
        if selected_format != "All":
            source_layers = [l for l in source_layers if selected_format in l.get("formats", "")]
        if selected_type != "All":
            source_layers = [l for l in source_layers if l.get("type") == selected_type]
        sources = set(l.get("source", "") for l in source_layers if l.get("source", ""))
        source_values = ["All"] + sorted(sources)

        # Format options: all formats present in layers matching current source and type
        format_layers = self.all_layers
        if selected_source != "All":
            format_layers = [l for l in format_layers if l.get("source") == selected_source]
        if selected_type != "All":
            format_layers = [l for l in format_layers if l.get("type") == selected_type]
        formats = set()
        for l in format_layers:
            fmt = l.get("formats", "")
            if isinstance(fmt, str):
                for f in fmt.split(","):
                    formats.add(f.strip())
            elif isinstance(fmt, list):
                for f in fmt:
                    formats.add(str(f).strip())
        format_values = ["All"] + sorted(f for f in formats if f)

        # Type options: all types present in layers matching current source and format
        type_layers = self.all_layers
        if selected_source != "All":
            type_layers = [l for l in type_layers if l.get("source") == selected_source]
        if selected_format != "All":
            type_layers = [l for l in type_layers if selected_format in l.get("formats", "")]
        types = set(l.get("type", "") for l in type_layers if l.get("type", ""))
        type_values = ["All"] + sorted(types)

        self.endpoint_combo['values'] = source_values
        self.format_combo['values'] = format_values
        self.type_combo['values'] = type_values

        # Reset selection if current value is not in the new list
        if self.endpoint_var.get() not in source_values:
            self.endpoint_var.set("All")
        if self.format_var.get() not in format_values:
            self.format_var.set("All")
        if self.type_var.get() not in type_values:
            self.type_var.set("All")

        self.apply_filters()

    def select_all(self):
        if not hasattr(self, "group_nodes"):
            return
        for group_id in self.group_nodes.values():
            for child in self.tree.get_children(group_id):
                self.tree.selection_add(child)

    def clear_selection(self):
        self.tree.selection_remove(self.tree.get_children())

    def fetch_layers(self):
        self.status_var.set("0%")
        self.progress["mode"] = "determinate"
        self.progress["value"] = 0
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
            fetch_ash3d_layers,
        ]
        layers = []
        total_fetchers = len(fetch_funcs)
        completed_fetchers = 0

        def progress_cb(percent, message):
            # This callback can be called by fetchers, but we update only on fetcher completion below
            pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=total_fetchers) as executor:
            futures = [executor.submit(f, progress_cb) for f in fetch_funcs]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                completed_fetchers += 1
                if isinstance(result, dict):
                    layers.extend(result['layers'])
                elif isinstance(result, list):
                    layers.extend(result)
                percent = int((completed_fetchers / total_fetchers) * 100)
                self.root.after(0, lambda p=percent: self.status_var.set(f"{p}%"))
                self.root.after(0, lambda p=percent: self.progress.config(value=p))
                self.root.after(0, lambda c=completed_fetchers, t=total_fetchers: self.progress_label.set(f"Fetched {c}/{t} sources..."))

        # Build dynamic source counts
        source_counts = {}
        for layer in layers:
            src = layer.get("source", "Unknown")
            source_counts[src] = source_counts.get(src, 0) + 1
        self.all_layers = layers
        self.source_counts = source_counts
        self.root.after(0, self._update_ui_after_fetch)

        # Detect changes and group by source
        changes = detect_new_or_updated_layers(layers)
        self.last_changes = changes

        # Build a map from layer_id to change type
        change_map = {}
        for c in changes:
            change_map[c.layer_id] = c.change_type

        # Mark display_name for each layer (for treeview)
        for layer in layers:
            key = f"{layer.get('source','')}|{layer.get('endpoint','')}|{layer.get('name','')}"
            change_type = change_map.get(key)
            if change_type == "NEW":
                layer["display_name"] = f"[NEW] {layer['name']}"
            elif change_type == "UPDATED":
                layer["display_name"] = f"[UPDATED] {layer['name']}"
            else:
                layer["display_name"] = layer["name"]

        # Group changes by source for summary popup
        changes_by_source = defaultdict(list)
        for c in changes:
            changes_by_source[c.source].append(c)

        # Build summary message (counts only)
        msg = ""
        for source, source_changes in changes_by_source.items():
            new = sum(1 for c in source_changes if c.change_type == "NEW")
            updated = sum(1 for c in source_changes if c.change_type == "UPDATED")
            if new or updated:
                msg += f"{source}: "
                if new:
                    msg += f"{new} new"
                if new and updated:
                    msg += ", "
                if updated:
                    msg += f"{updated} updated"
                msg += "\n"

        msg += (
            "\nRemember, this is thrown together by a non-nerd! If a real nerd wants to take over, "
            "please let me add them as contributor on Github. Also, D.J. loves you! ❤️"
        )

        if msg.strip() and changes:
            self.root.after(0, lambda: messagebox.showinfo("Change Summary", msg))

    def _update_ui_after_fetch(self):
        total = sum(self.source_counts.values())
        if total == 0:
            self.counter_var.set("No layers loaded yet!")
        else:
            counts_str = " | ".join(
                f"{src}: {count}" for src, count in sorted(self.source_counts.items()) if count > 0
            )
            self.counter_var.set(f"{counts_str} | Total: {total}")
        self.progress.stop()
        self.progress["value"] = 100
        self.status_var.set(f"Found {total} layers")
        self.progress_label.set("")
        self.update_filter_options()
        self.apply_filters()

    def apply_filters(self):
        endpoint = self.endpoint_var.get()
        fmt = self.format_var.get()
        typ = self.type_var.get()
        search = self.search_var.get().lower()
        self.filtered_layers = []
        for layer in self.all_layers:
            if endpoint != "All" and layer.get("source") != endpoint:
                continue
            if fmt != "All" and fmt not in layer.get("formats", ""):
                continue
            if typ != "All" and typ != layer.get("type", ""):
                continue
            if search and search not in layer.get("name", "").lower():
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
            for layer in sorted(groups[group], key=lambda l: l.get("name", "").lower()):
                self.tree.insert(
                    group_id,
                    tk.END,
                    values=(
                        layer.get("display_name", layer.get("name", "")),
                        layer.get("type", ""),
                        layer.get("endpoint", ""),
                        layer.get("formats", "")
                    )
                )

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
        layer = next((l for l in self.filtered_layers if l.get("display_name", l["name"]) == values[0] and l["endpoint"] == values[2]), None)
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
            # If this is a group node (category), export all its children
            if not values or not values[0]:
                for child in self.tree.get_children(sel):
                    child_item = self.tree.item(child)
                    child_values = child_item["values"]
                    if not child_values or not child_values[0]:
                        continue
                    layer = next((l for l in self.filtered_layers if l.get("display_name", l["name"]) == child_values[0] and l["endpoint"] == child_values[2]), None)
                    if layer:
                        layers.append(layer)
            else:
                layer = next((l for l in self.filtered_layers if l.get("display_name", l["name"]) == values[0] and l["endpoint"] == values[2]), None)
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

    def export_changes(self):
        if not hasattr(self, "last_changes") or not self.last_changes:
            messagebox.showinfo("Export Changes", "No changes to export. Please fetch layers first.")
            return

        formats = [("CSV", "*.csv"), ("Excel", "*.xlsx"), ("JSON", "*.json"), ("Text", "*.txt"), ("Word", "*.docx"), ("PDF", "*.pdf")]
        filetypes = formats
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=filetypes)
        if not file_path:
            return

        try:
            from .export import export_changes as export_changes_func
            fmt = file_path.split('.')[-1].lower()
            export_changes_func(self.last_changes, fmt, Path(file_path))
            messagebox.showinfo("Export Changes", f"Exported {len(self.last_changes)} changes to {file_path}")
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
