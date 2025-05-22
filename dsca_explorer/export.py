# dsca_explorer/export.py

import pandas as pd
import json
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from urllib.parse import urlparse
from html.parser import HTMLParser
from io import StringIO
import markdown
from markdown import Markdown

# HTML stripping utilities
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()
    
    def handle_data(self, d):
        self.text.write(d)
    
    def get_data(self):
        return self.text.getvalue()

def strip_html(html):
    if not html:
        return ""
    s = MLStripper()
    s.feed(html)
    return s.get_data()

# Markdown to plain text conversion
def unmark_element(element, stream=None):
    if stream is None:
        stream = StringIO()
    if element.text:
        stream.write(element.text)
    for sub in element:
        unmark_element(sub, stream)
    if element.tail:
        stream.write(element.tail)
    return stream.getvalue()

Markdown.output_formats["plain"] = unmark_element
__md = Markdown(output_format="plain")
__md.stripTopLevelTags = False

def clean_description(desc):
    """Convert Markdown to HTML then strip all tags"""
    if not desc:
        return ""
    try:
        # Convert Markdown to HTML
        html = markdown.markdown(desc)
        # Strip HTML tags
        return strip_html(html).strip()
    except Exception:
        return strip_html(desc).strip()

# Core export functions
def get_domain(url):
    try:
        return urlparse(url).netloc
    except Exception:
        return ""

def get_arcgis_compat(endpoint):
    if not endpoint:
        return ""
    if "/MapServer" in endpoint or "/FeatureServer" in endpoint:
        return "ArcGIS Service"
    elif "arcgis.com" in endpoint:
        return "ArcGIS REST API"
    else:
        return "REST API"

def get_property_list(properties):
    """Extract meaningful properties from layer/feature data"""
    if not properties:
        return ""
    
    # Handle layer fields definition
    if isinstance(properties, dict) and "fields" in properties:
        field_names = [field.get("name", "") 
                      for field in properties["fields"]
                      if isinstance(field, dict)]
        return ", ".join(sorted(field_names))
    
    # Handle feature attributes
    if isinstance(properties, dict) and "features" in properties:
        if properties["features"] and isinstance(properties["features"][0], dict):
            attrs = properties["features"][0].get("attributes", {})
            return ", ".join(sorted(attrs.keys()))
    
    # Fallback to property keys
    if isinstance(properties, dict):
        return ", ".join(sorted(properties.keys()))
    
    return ""

def export_layers(layers, file_path):
    ext = file_path.split('.')[-1].lower()
    
    processed_layers = []
    for l in layers:
        processed = {
            "Source": l.get("source", ""),
            "Series": l.get("series", ""),
            "Layer Name": l.get("name", ""),
            "Type": l.get("type", ""),
            "Endpoint": l.get("endpoint", ""),
            "Domain": get_domain(l.get("endpoint", "")),
            "ArcGIS Compatible": get_arcgis_compat(l.get("endpoint", "")),
            "Download URL": l.get("download_url", l.get("endpoint", "")),
            "Documentation": l.get("documentation", ""),
            "Description": clean_description(l.get("description", "")),
            "Property List": get_property_list(l.get("properties", {})),
            "Example Properties": json.dumps(l.get("properties", {}), ensure_ascii=False)
        }
        processed_layers.append(processed)
    
    df = pd.DataFrame(processed_layers)
    
    if ext == "csv":
        df.to_csv(file_path, index=False)
    elif ext == "xlsx":
        df.to_excel(file_path, index=False)
    elif ext == "json":
        with open(file_path, "w") as f:
            json.dump(processed_layers, f, indent=2, ensure_ascii=False)
    elif ext == "txt":
        with open(file_path, "w") as f:
            for l in processed_layers:
                f.write(
                    f"Source: {l['Source']}\n"
                    f"Series: {l['Series']}\n"
                    f"Name: {l['Layer Name']}\n"
                    f"Type: {l['Type']}\n"
                    f"Endpoint: {l['Endpoint']}\n"
                    f"Domain: {l['Domain']}\n"
                    f"ArcGIS Compatible: {l['ArcGIS Compatible']}\n"
                    f"Download URL: {l['Download URL']}\n"
                    f"Documentation: {l['Documentation']}\n"
                    f"Description: {l['Description']}\n"
                    f"Property List: {l['Property List']}\n"
                    f"Properties: {l['Example Properties']}\n\n"
                )
    elif ext == "docx":
        doc = Document()
        doc.add_heading("DSCA Exported Layers", 0)
        for l in processed_layers:
            doc.add_heading(l['Layer Name'], level=1)
            doc.add_paragraph(f"Source: {l['Source']}")
            doc.add_paragraph(f"Series: {l['Series']}")
            doc.add_paragraph(f"Type: {l['Type']}")
            doc.add_paragraph(f"Endpoint: {l['Endpoint']}")
            doc.add_paragraph(f"Domain: {l['Domain']}")
            doc.add_paragraph(f"ArcGIS Compatible: {l['ArcGIS Compatible']}")
            doc.add_paragraph(f"Download URL: {l['Download URL']}")
            doc.add_paragraph(f"Documentation: {l['Documentation']}")
            doc.add_paragraph(f"Description: {l['Description']}")
            doc.add_paragraph(f"Property List: {l['Property List']}")
            doc.add_paragraph(f"Properties: {l['Example Properties']}")
        doc.save(file_path)
    elif ext == "pdf":
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        y = height - 40
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, y, "DSCA Exported Layers")
        y -= 30
        c.setFont("Helvetica", 10)
        for l in processed_layers:
            if y < 100:
                c.showPage()
                y = height - 40
            for key in ["Source", "Series", "Layer Name", "Type", 
                       "Endpoint", "Domain", "ArcGIS Compatible",
                       "Download URL", "Documentation", "Description",
                       "Property List"]:
                c.drawString(40, y, f"{key}: {l.get(key, '')}")
                y -= 15
            props = l.get("Example Properties", "{}")
            for line in props.splitlines():
                if y < 100:
                    c.showPage()
                    y = height - 40
                c.drawString(60, y, line[:100])
                y -= 12
            y -= 10
        c.save()
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
