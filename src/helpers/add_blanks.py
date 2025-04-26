import json
import csv
import os
import re

# --- CONFIGURATION ---
metadata_file = "collection_metadata.json"
output_csv = "supervised_annotations.csv"
base_dir = "Manuscripts/I. Manuscripts"

# --- LOAD METADATA ---
with open(metadata_file, "r", encoding="utf-8") as f:
    items = json.load(f)

rows = []

# --- PROCESS ITEMS ---
for item in items:
    if item.get("Category Level 1") != "I. Manuscripts":
        continue

    item_id = item.get("ID")
    category = item.get("Category Level 2", "").strip()
    canvas_list = item.get("Canvas", [])

    if not item_id or not category or not canvas_list:
        continue

    item_folder = os.path.join(base_dir, category, item_id)

    for canvas in canvas_list:
        canvas_label = canvas.get("Label", "")
        filename = canvas.get("Filename", "")

        if not filename:
            continue

        image_path = os.path.join(item_folder, filename)

        # Check if the canvas label indicates a blank page
        if "blank" in canvas_label.lower():
            label = "blank"
        else:
            label = ""

        rows.append({
            "ID": item_id,
            "Image Path": image_path,
            "Canvas Label": canvas_label,
            "Filename": filename,
            "Annotated Label": label
        })

# --- WRITE CSV ---
with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["ID", "Image Path", "Canvas Label", "Filename", "Annotated Label"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ CSV written to: {output_csv} with {len(rows)} entries.")
