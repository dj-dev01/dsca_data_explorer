# dsca_explorer/export.py

import pandas as pd
import json
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_layers(layers, file_path):
    ext = file_path.split('.')[-1].lower()
    df = pd.DataFrame([
        {
            "Source": l.get("source", ""),
            "Series": l.get("series", ""),
            "Layer Name": l.get("name", ""),
            "Type": l.get("type", ""),
            "Endpoint": l.get("endpoint", ""),
            "Download URL": l.get("download_url", l.get("endpoint", "")),
            "Documentation": l.get("documentation", ""),
            "Description": l.get("description", ""),
            "Example Properties": json.dumps(l.get("properties", {}))
        } for l in layers
    ])
    if ext == "csv":
        df.to_csv(file_path, index=False)
    elif ext == "xlsx":
        df.to_excel(file_path, index=False)
    elif ext == "json":
        with open(file_path, "w") as f:
            json.dump(layers, f, indent=2)
    elif ext == "txt":
        with open(file_path, "w") as f:
            for l in layers:
                f.write(f"Source: {l.get('source','')}\nSeries: {l.get('series','')}\nName: {l.get('name','')}\nType: {l.get('type','')}\nEndpoint: {l.get('endpoint','')}\nDownload URL: {l.get('download_url','')}\nDocumentation: {l.get('documentation','')}\nDescription: {l.get('description','')}\nProperties: {json.dumps(l.get('properties',{}), indent=2)}\n\n")
    elif ext == "docx":
        doc = Document()
        doc.add_heading("DSCA Exported Layers", 0)
        for l in layers:
            doc.add_heading(l.get('name',''), level=1)
            doc.add_paragraph(f"Source: {l.get('source','')}")
            doc.add_paragraph(f"Series: {l.get('series','')}")
            doc.add_paragraph(f"Type: {l.get('type','')}")
            doc.add_paragraph(f"Endpoint: {l.get('endpoint','')}")
            doc.add_paragraph(f"Download URL: {l.get('download_url','')}")
            doc.add_paragraph(f"Documentation: {l.get('documentation','')}")
            doc.add_paragraph(f"Description: {l.get('description','')}")
            doc.add_paragraph(f"Properties: {json.dumps(l.get('properties',{}), indent=2)}")
        doc.save(file_path)
    elif ext == "pdf":
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        y = height - 40
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, y, "DSCA Exported Layers")
        y -= 30
        c.setFont("Helvetica", 10)
        for l in layers:
            if y < 100:
                c.showPage()
                y = height - 40
            c.drawString(40, y, f"Source: {l.get('source','')}")
            y -= 15
            c.drawString(40, y, f"Series: {l.get('series','')}")
            y -= 15
            c.drawString(40, y, f"Name: {l.get('name','')}")
            y -= 15
            c.drawString(40, y, f"Type: {l.get('type','')}")
            y -= 15
            c.drawString(40, y, f"Endpoint: {l.get('endpoint','')}")
            y -= 15
            c.drawString(40, y, f"Download URL: {l.get('download_url','')}")
            y -= 15
            c.drawString(40, y, f"Documentation: {l.get('documentation','')}")
            y -= 15
            desc = l.get('description','')
            if desc:
                c.drawString(40, y, f"Description: {desc[:100]}")
                y -= 15
            props = json.dumps(l.get('properties',{}), indent=2)
            for line in props.splitlines():
                if y < 100:
                    c.showPage()
                    y = height - 40
                c.drawString(60, y, line[:100])
                y -= 12
            y -= 10
        c.save()
    else:
        raise ValueError("Unsupported file extension.")
