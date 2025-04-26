import os
import json
import joblib
import pandas as pd
from tqdm import tqdm
from PIL import Image
from sklearn.preprocessing import LabelEncoder
import torch
import clip

# --- CONFIGURATION ---
metadata_path = "collection_metadata.json"
manuscripts_root = "Manuscripts/I. Manuscripts"
output_filtered_csv = "filtered_candidates.csv"
model_path = "clip_svm_classifier.pkl"
encoder_path = "label_encoder.pkl"

# --- LOAD CLIP MODEL ---
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model, preprocess = clip.load("ViT-B/32", device=device)

# --- LOAD CLASSIFIER AND ENCODER ---
with open(model_path, "rb") as f:
    classifier = joblib.load(f)

with open(encoder_path, "rb") as f:
    label_encoder: LabelEncoder = joblib.load(f)

# --- TARGET LABELS TO FILTER ---
target_labels = ["cover", "diagram", "sketch"]
target_indices = [label_encoder.transform([lbl])[0] for lbl in target_labels]

# --- LOAD METADATA ---
with open(metadata_path, "r", encoding="utf-8") as f:
    metadata = json.load(f)

# --- COLLECT IMAGE PATHS ---
images = []
for item in metadata:
    if item.get("Category Level 1") != "I. Manuscripts":
        continue

    item_id = item.get("ID", "")
    category = item.get("Category Level 2", "").strip()
    canvas = item.get("Canvas", [])

    for entry in canvas:
        filename = entry.get("Filename", "")
        label = entry.get("Label", "")
        image_path = os.path.join(manuscripts_root, category, item_id, filename)

        if os.path.exists(image_path):
            images.append({
                "ID": item_id,
                "Image Path": image_path,
                "Canvas Label": label,
                "Filename": filename
            })

# --- CLASSIFY IMAGES AND FILTER ---
candidates = []

for img in tqdm(images, desc="Classifying images"):
    try:
        image = preprocess(Image.open(img["Image Path"]).convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            image_features = clip_model.encode_image(image).cpu().numpy()
        prediction = classifier.predict(image_features)[0]
        if prediction in target_indices:
            label_name = label_encoder.inverse_transform([prediction])[0]
            img["Predicted Label"] = label_name
            candidates.append(img)
    except Exception as e:
        print(f"⚠️ Failed to process {img['Image Path']}: {e}")

# --- SAVE CSV ---
df = pd.DataFrame(candidates)
df.to_csv(output_filtered_csv, index=False)
print(f"✅ Saved {len(candidates)} filtered candidates to {output_filtered_csv}")
