import os
import json
import torch
import clip
import joblib
import pandas as pd
from PIL import Image
from tqdm import tqdm
import re

# === CONFIG ===
MANUSCRIPTS_DIR = "Manuscripts"
METADATA_FILE = "metadata_updated.json"
OUTPUT_METADATA = "metadata_with_predictions.json"
MODEL_PATH = "clip_svm_classifier.pkl"
ENCODER_PATH = "label_encoder.pkl"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# === Carica modello CLIP e SVM ===
print("🔁 Caricamento modello CLIP + SVM...")
model_clip, preprocess = clip.load("ViT-B/32", device=DEVICE)
clf = joblib.load(MODEL_PATH)
le = joblib.load(ENCODER_PATH)

# === Carica metadati ===
with open(METADATA_FILE, "r") as f:
    metadata = json.load(f)

# === Trova la cartella dell'item in base al label ===
def find_item_folder(category, target_label):
    category_path = os.path.join(MANUSCRIPTS_DIR, category)
    if not os.path.exists(category_path):
        print(f"❌ Categoria non trovata: {category_path}")
        return None
    for subfolder in os.listdir(category_path):
        subfolder_path = os.path.join(category_path, subfolder)
        manifest_path = os.path.join(subfolder_path, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r") as f:
                    data = json.load(f)
                    if data.get("label") == target_label:
                        return subfolder_path
            except Exception as e:
                print(f"⚠️ Errore leggendo manifest in {subfolder_path}: {e}")
                continue
    return None

# === Classificazione corpus ===
classification_records = []

for item in tqdm(metadata, desc="📂 Classifying corpus"):
    manifest_uri = item["Manifest URI"]
    match = re.search(r"(ids|drs):(\d+)", manifest_uri)
    if not match:
        print(f"❌ Manifest ID non trovato in {manifest_uri}")
        continue

    manifest_id = match.group(2)
    category = item["Category"]
    item_title = item["label"]

    # Trova la cartella giusta
    item_folder = find_item_folder(category, item_title)
    if not item_folder:
        print(f"⚠️ Cartella non trovata per item: {item_title}")
        continue

    canvas_metadata_path = os.path.join(item_folder, f"{manifest_id}.json")
    if not os.path.exists(canvas_metadata_path):
        print(f"⚠️ Canvas metadata non trovato: {canvas_metadata_path}")
        continue

    try:
        with open(canvas_metadata_path, "r") as f:
            canvas_data = json.load(f)
    except Exception as e:
        print(f"❌ Errore nel JSON {canvas_metadata_path}: {e}")
        continue

    canvas_predictions = []

    for canvas in canvas_data:
        img_path = os.path.join(item_folder, canvas["Image Filename"])
        if not os.path.exists(img_path):
            print(f"🚫 Immagine non trovata: {img_path}")
            pred = "missing"
        else:
            try:
                image = preprocess(Image.open(img_path).convert("RGB")).unsqueeze(0).to(DEVICE)
                with torch.no_grad():
                    embedding = model_clip.encode_image(image).cpu().numpy().flatten().reshape(1, -1)
                pred_idx = clf.predict(embedding)[0]
                pred = le.inverse_transform([pred_idx])[0]
                print(f"🖼️ {canvas['Image Filename']} → {pred}")
            except Exception as e:
                print(f"❌ Errore su {img_path}: {e}")
                pred = "error"

        canvas_predictions.append({
            "Canvas Label": canvas["Canvas Label"],
            "Image Filename": canvas["Image Filename"],
            "Prediction": pred
        })

        classification_records.append({
            "Item": item_title,
            "Category": category,
            "Manifest ID": manifest_id,
            "Canvas Label": canvas["Canvas Label"],
            "Image Filename": canvas["Image Filename"],
            "Prediction": pred
        })

    item["Canvas Predictions"] = canvas_predictions

# === Salva nuovo metadata con predizioni ===
with open(OUTPUT_METADATA, "w") as f:
    json.dump(metadata, f, indent=4, ensure_ascii=False)
print(f"✅ File {OUTPUT_METADATA} salvato.")

# === Salva CSV ===
df = pd.DataFrame(classification_records)
df.to_csv("svm_classification_results.csv", index=False)
print("📄 File svm_classification_results.csv salvato.")
