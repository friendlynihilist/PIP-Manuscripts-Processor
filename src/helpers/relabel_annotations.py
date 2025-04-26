import csv

# --- CONFIGURATION ---
input_csv = "supervised_annotations.csv"
output_csv = "supervised_annotations_relabelled.csv"

# --- RELABEL MAP ---
relabel_map = {
    "diagram": "diagram_mixed",
    "mixed": "diagram_mixed",
    "sketch": "diagram_mixed",
    "text": "text",
    "cover": "cover",
}

# --- PROCESS ---
with open(input_csv, newline='', encoding='utf-8') as infile, \
     open(output_csv, "w", newline='', encoding='utf-8') as outfile:

    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        original_label = row["Annotated Label"].strip().lower()
        
        if original_label in relabel_map:
            row["Annotated Label"] = relabel_map[original_label]
            writer.writerow(row)
        elif original_label == "sketch":
            # Skip sketches for now
            print(f"🗑️ Skipped sketch: {row['Image Path']}")
        elif original_label == "blank":
            # Keep blanks untouched if any
            writer.writerow(row)
        else:
            print(f"⚠️ Unknown label: {original_label}")

print("✅ Relabelling complete! Output saved to:", output_csv)
