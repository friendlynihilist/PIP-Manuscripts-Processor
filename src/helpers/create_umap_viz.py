import os
import json
import torch
import clip
import numpy as np
import umap
import matplotlib.pyplot as plt
from PIL import Image
from tqdm import tqdm

# === CONFIG ===
METADATA_FILE = "metadata_with_predictions.json"
MANUSCRIPTS_DIR = "Manuscripts"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# === Load CLIP model ===
print("🔁 Loading CLIP...")
model, preprocess = clip.load("ViT-B/32", device=DEVICE)

# === Load metadata ===
with open(METADATA_FILE, "r") as f:
    metadata = json.load(f)

embeddings = []
labels = []
filenames = []

print("📥 Extracting embeddings...")

for item in tqdm(metadata):
    category = item["Category"]
    label = item["label"]
    folder_found = False

    # Sanity check: trova cartella dell'item
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
        img_path = os.path.join(subfolder_path, canvas["Image Filename"])

        if not os.path.exists(img_path):
            continue

        try:
            image = preprocess(Image.open(img_path).convert("RGB")).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                embedding = model.encode_image(image).cpu().numpy().flatten()
            embeddings.append(embedding)
            labels.append(pred_label)
            filenames.append(canvas["Image Filename"])
        except Exception as e:
            print(f"❌ Errore su {img_path}: {e}")

# === Run UMAP ===
print("🧭 Running UMAP...")
reducer = umap.UMAP(random_state=42)
embedding_2d = reducer.fit_transform(embeddings)

# === Plot ===
print("📊 Plotting...")
plt.figure(figsize=(10, 8))
unique_labels = list(set(labels))
colors = plt.cm.get_cmap('tab10', len(unique_labels))

for i, label_name in enumerate(unique_labels):
    idxs = [j for j, l in enumerate(labels) if l == label_name]
    plt.scatter(
        [embedding_2d[j, 0] for j in idxs],
        [embedding_2d[j, 1] for j in idxs],
        label=label_name,
        s=20,
        alpha=0.7,
        c=[colors(i)]
    )

plt.title("UMAP projection of CLIP embeddings")
plt.legend()
plt.tight_layout()
plt.savefig("clip_umap_projection.png", dpi=300)
plt.show()
