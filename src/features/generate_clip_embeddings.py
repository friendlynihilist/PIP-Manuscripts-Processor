import os
import json
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm
import torch
import open_clip

# === Configuration ===
metadata_path = "../../data/processed/collection_metadata.json"
base_image_dir = "../../data/raw/Manuscripts"
output_embeddings = "../../data/processed/clip_embeddings_full.npy"
output_metadata = "../../data/processed/clip_embedding_index.csv"

device = "cuda" if torch.cuda.is_available() else "cpu"

# === Load CLIP model ===
model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai")
model.eval().to(device)

# === Load metadata ===
with open(metadata_path, "r") as f:
    metadata = json.load(f)

# === Prepare storage ===
clip_embeddings = []
records = []

# === Process each manuscript item ===
for item in tqdm(metadata, desc="Processing manuscript items"):
    cat1 = item.get("Category Level 1", "").strip()
    cat2 = item.get("Category Level 2", "").strip()
    item_id = item["ID"]
    canvas_list = item.get("Canvas", [])

    for canvas in canvas_list:
        filename = canvas["Filename"]
        page_label = canvas.get("Label", "")

        # Construct full path
        image_path = os.path.join(base_image_dir, cat1, cat2, item_id, filename)

        if not os.path.isfile(image_path):
            print(f"⚠️ Missing: {image_path}")
            continue

        try:
            img = Image.open(image_path).convert("RGB")
            img_tensor = preprocess(img).unsqueeze(0).to(device)

            with torch.no_grad():
                embedding = model.encode_image(img_tensor).cpu().numpy().flatten()

            clip_embeddings.append(embedding)
            records.append({
                "Path": image_path,
                "ID": item_id,
                "Filename": filename,
                "Label": page_label,
                "Category Level 1": cat1,
                "Category Level 2": cat2
            })

        except Exception as e:
            print(f"❌ Failed to process {image_path}: {e}")

# === Save results ===
np.save(output_embeddings, np.array(clip_embeddings))
pd.DataFrame(records).to_csv(output_metadata, index=False)

print(f"\n✅ Saved {len(clip_embeddings)} CLIP embeddings to {output_embeddings}")
print(f"✅ Saved metadata index to {output_metadata}")