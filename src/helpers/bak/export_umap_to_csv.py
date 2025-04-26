import os
import json
import torch
import clip
import numpy as np
import umap
import pandas as pd
from PIL import Image
from tqdm import tqdm

# === CONFIG ===
METADATA_FILE = "metadata_with_predictions.json"
MANUSCRIPTS_DIR = "Manuscripts"
OUTPUT_CSV = "umap_projection_data.csv"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# === Carica CLIP ===
print("🔁 Caricamento CLIP...")
model, preprocess = clip.load("ViT-B/32", device=DEVICE)

# === Carica metadati ===
with open(METADATA_FILE, "r") as f:
    metadata = json.load(f)

embeddings = []
records = []

print("📥 Estrazione embeddings...")

for item in tqdm(metadata):
    category = item["Category"]
    label = item["label"]
    folder_found = False

    category_path = os.path.join(MANUSCRIPTS_DIR, category)
    if not os.path.exists(category_path):
        continue

    for subfolder in os.listdir(category_path):
        subfolder_path = os.path.join(category_path, subfolder)
        manifest_path = os.path.join(subfolder_path, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r") as f:
                manifest_data = json.load(f)
                if manifest_data.get("label") == label:
                    folder_found = True
                    break

    if not folder_found:
        continue

    for canvas in item.get("Canvas Predictions", []):
        pred_label = canvas.get("Prediction", "")
        filename = canvas.get("Image Filename", "")
        canvas_label = canvas.get("Canvas Label", "")
        img_path = os.path.join(subfolder_path, filename)

        if not os.path.exists(img_path):
            continue

        try:
            image = preprocess(Image.open(img_path).convert("RGB")).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                embedding = model.encode_image(image).cpu().numpy().flatten()
            embeddings.append(embedding)
            records.append({
                "Image Filename": filename,
                "Prediction": pred_label,
                "Manifest ID": item["Manifest URI"],
                "Canvas Label": canvas_label
            })
        except Exception as e:
            print(f"⚠️ Errore su {img_path}: {e}")

# === UMAP ===
print("🧭 UMAP in corso...")
reducer = umap.UMAP(random_state=42)
embedding_2d = reducer.fit_transform(embeddings)

# === Salva CSV ===
df = pd.DataFrame(records)
df["UMAP X"] = embedding_2d[:, 0]
df["UMAP Y"] = embedding_2d[:, 1]
df.to_csv(OUTPUT_CSV, index=False)

print(f"✅ CSV salvato in: {OUTPUT_CSV}")