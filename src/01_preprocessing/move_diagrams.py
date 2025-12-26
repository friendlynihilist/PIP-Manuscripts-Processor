import os
import shutil
import pandas as pd
from PIL import Image
from pathlib import Path
from hashlib import sha256

# === CONFIGURATION ===
classified_csv = "../../data/results/classified_pages.csv"  # Path to your classification results
output_dir = "../../data/derived/layout_input"              # Folder where extracted pages go
manifest_csv = "../../data/derived/layout_input_manifest.csv"  # Log file
os.makedirs(output_dir, exist_ok=True)

# === Load classified data ===
df = pd.read_csv(classified_csv)
diagram_df = df[df["Predicted_Label"] == "diagram_mixed"]

print(f"📄 Found {len(diagram_df)} pages labeled as 'diagram_mixed'.")

# === Prepare manifest entries ===
manifest_entries = []

# === Iterate and copy ===
for _, row in diagram_df.iterrows():
    original_path = row["Path"]
    category = row["Category Level 2"].strip().replace(" ", "_")
    item_id = row["ID"]
    filename = row["Filename"]

    # Build new filename (traceable and unique)
    new_filename = f"{category}__{item_id}__{filename}"
    destination_path = os.path.join(output_dir, new_filename)

    # Validate and copy
    if not os.path.isfile(original_path):
        print(f"⚠️ Missing file: {original_path}")
        continue

    try:
        # Check image validity
        with Image.open(original_path) as img:
            img.verify()  # Will raise if corrupt

        # Copy file
        shutil.copy2(original_path, destination_path)

        # Compute hash for integrity (optional but useful)
        with open(destination_path, "rb") as f:
            file_hash = sha256(f.read()).hexdigest()

        # Record manifest entry
        manifest_entries.append({
            "local_filename": new_filename,
            "original_path": original_path,
            "category": row["Category Level 2"],
            "id": item_id,
            "filename": filename,
            "sha256": file_hash
        })

    except Exception as e:
        print(f"❌ Failed to process {original_path}: {e}")

# === Save manifest ===
manifest_df = pd.DataFrame(manifest_entries)
manifest_df.to_csv(manifest_csv, index=False)

print(f"\n✅ Copied {len(manifest_df)} files to: {output_dir}")
print(f"📝 Manifest saved to: {manifest_csv}")