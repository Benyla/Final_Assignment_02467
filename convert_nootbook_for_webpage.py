import os
from nbconvert import HTMLExporter
from nbformat import read
from pathlib import Path

# ─── Config ───────────────────────────────────────────────
notebook_path = "Explainer_notebook.ipynb"
output_path   = "web/explainer.html"

# Ensure output folder exists
Path(output_path).parent.mkdir(parents=True, exist_ok=True)

# ─── Load and convert ─────────────────────────────────────
with open(notebook_path, encoding="utf-8") as f:
    notebook_node = read(f, as_version=4)

html_exporter = HTMLExporter()
html_exporter.template_name = "lab"  # or 'classic'

(body, resources) = html_exporter.from_notebook_node(notebook_node)

# ─── Save HTML ────────────────────────────────────────────
with open(output_path, "w", encoding="utf-8") as f:
    f.write(body)

print(f"✅ Notebook converted to → {output_path}")