import os
import json
import random
import shutil
import clip
import torch
import pandas as pd
from PIL import Image
from tqdm import tqdm

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANUSCRIPTS_DIR = os.path.join(BASE_DIR, "Manuscripts")
METADATA_FILE = os.path.join(BASE_DIR, "metadata_updated.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "manual_annotation")
CSV_OUTPUT = os.path.join(OUTPUT_DIR, "manual_annotation_labels.csv")

SAMPLES_PER_CLASS = {
    "text": 50,
    "diagram": 50,
    "sketch": 30,
    "cover": 20,
    "blank": 20
}

# PROMPT SETS
prompt_sets = {
    "diagram": [
        "a historical manuscript page with hand-drawn diagrams",
        "a page showing scientific or logical diagrams",
        "a visual diagram in a manuscript",
        "a sketch with arrows, boxes, or symbols",
        "a page of abstract visual structures"
    ],
    "text": [
        "a page of handwritten philosophical text",
        "a handwritten page from a 19th-century notebook",
        "a manuscript page filled with cursive writing",
        "a page with symbolic mathematical notation",
        "a manuscript containing numeric formulas and calculations",
        "a manuscript page with equations and variables"
    ],
    "sketch": [
        "a manuscript page with casual sketches or doodles",
        "a page with marginal drawings or caricatures",
        "a page containing visual flourishes or decorative elements",
        "a handwritten note with small figures or symbols",
        "a manuscript with imaginative or playful drawings"
    ],
    "cover": [
        "a manuscript cover page with a title",
        "an old manuscript book cover",
        "the first page of a manuscript with a title"
    ],
    "blank": [
        "a completely blank manuscript page",
        "a page with no writing or drawing",
        "an empty page of a notebook"
    ]
}

def compute_category_embeddings(model, device):
    category_embeddings = {}
    for cat, prompts in prompt_sets.items():
        tokens = clip.tokenize(prompts).to(device)
        with torch.no_grad():
            embeddings = model.encode_text(tokens)
            mean_embedding = embeddings.mean(dim=0)
            category_embeddings[cat] = mean_embedding / mean_embedding.norm()
    return category_embeddings

def classify_image_clip(model, preprocess, image_path, category_embeddings, device):
    try:
        image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
        with torch.no_grad():
            image_features = model.encode_image(image)
            image_features /= image_features.norm(dim=-1, keepdim=True)
        scores = {cat: (image_features @ emb.unsqueeze(0).T).item()
                  for cat, emb in category_embeddings.items()}
        prediction = max(scores, key=scores.get)
        return prediction, scores
    except Exception as e:
        print(f"Error classifying {image_path}: {e}")
        return None, None

def extract_samples():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    category_embeddings = compute_category_embeddings(model, device)

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    selected_counts = {cat: 0 for cat in SAMPLES_PER_CLASS}
    results = []

    all_candidates = []

    for item in metadata:
        category = item["Category"]
        label = item["label"]
        manifest_uri = item["Manifest URI"]
        manifest_id = manifest_uri.split(":")[-1]

        category_path = os.path.join(MANUSCRIPTS_DIR, category)
        for subfolder in os.listdir(category_path):
            item_folder = os.path.join(category_path, subfolder)
            manifest_json = os.path.join(item_folder, f"{manifest_id}.json")
            if os.path.exists(manifest_json):
                with open(manifest_json, "r", encoding="utf-8") as mf:
                    canvas_data = json.load(mf)
                for canvas in canvas_data:
                    img_file = canvas.get("Image Filename")
                    img_path = os.path.join(item_folder, img_file)
                    if os.path.exists(img_path):
                        all_candidates.append((img_path, label))
                break

    random.shuffle(all_candidates)

    for img_path, label in tqdm(all_candidates, desc="Classifying and copying"):
        pred, scores = classify_image_clip(model, preprocess, img_path, category_embeddings, device)
        if not pred:
            continue
        if selected_counts[pred] >= SAMPLES_PER_CLASS[pred]:
            continue

        pred_dir = os.path.join(OUTPUT_DIR, pred)
        os.makedirs(pred_dir, exist_ok=True)
        filename = f"{pred}_{selected_counts[pred]+1:03}.jpg"
        dst_path = os.path.join(pred_dir, filename)
        shutil.copy(img_path, dst_path)

        results.append({
            "filename": filename,
            "original_path": img_path,
            "predicted_label": pred,
            "manifest": label,
            **{f"score_{k}": round(v, 4) for k, v in scores.items()}
        })

        selected_counts[pred] += 1
        if all(selected_counts[c] >= SAMPLES_PER_CLASS[c] for c in SAMPLES_PER_CLASS):
            break

    pd.DataFrame(results).to_csv(CSV_OUTPUT, index=False)
    print(f"✅ Estrazione completata: {len(results)} immagini annotate in {OUTPUT_DIR}")
    print(f"📄 CSV con classificazioni salvato in: {CSV_OUTPUT}")

if __name__ == "__main__":
    extract_samples()
