import os
import json
import clip
import torch
from PIL import Image
import pandas as pd
from tqdm import tqdm

# ---------- CONFIG ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MANUSCRIPTS_DIR = os.path.join(SCRIPT_DIR, "Manuscripts")
METADATA_FILE = os.path.join(SCRIPT_DIR, "metadata_updated.json")
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "clip_classification_summary.csv")

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# ---------- PROMPT SET ----------
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

# ---------- PRECOMPUTE TEXT EMBEDDINGS ----------
def compute_category_embeddings():
    category_embeddings = {}
    for category, prompts in prompt_sets.items():
        tokens = clip.tokenize(prompts).to(device)
        with torch.no_grad():
            embeddings = model.encode_text(tokens)
            mean_embedding = embeddings.mean(dim=0)
            category_embeddings[category] = mean_embedding / mean_embedding.norm()
    return category_embeddings

category_embeddings = compute_category_embeddings()

# ---------- CLASSIFY IMAGE ----------
def classify_with_clip(image_path):
    try:
        image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
        with torch.no_grad():
            image_features = model.encode_image(image)
            image_features /= image_features.norm(dim=-1, keepdim=True)

        scores = {}
        for category, embedding in category_embeddings.items():
            similarity = (image_features @ embedding.unsqueeze(0).T).item()
            scores[category] = similarity

        prediction = max(scores, key=scores.get)
        return {
            "prediction": prediction,
            "scores": scores
        }

    except Exception as e:
        print(f"[ERROR] {image_path}: {e}")
        return None

# ---------- MAIN ----------
def main():
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    updated_metadata = []
    csv_rows = []

    for item in tqdm(metadata, desc="Processing manuscripts"):
        category = item["Category"]
        label = item["label"]
        manifest_uri = item["Manifest URI"]
        manifest_id = manifest_uri.split(":")[-1]

        category_path = os.path.join(MANUSCRIPTS_DIR, category)
        matched_folder = None
        for folder in os.listdir(category_path):
            folder_path = os.path.join(category_path, folder)
            if os.path.isdir(folder_path) and os.path.exists(os.path.join(folder_path, f"{manifest_id}.json")):
                matched_folder = folder_path
                break

        if not matched_folder:
            continue

        canvas_json_path = os.path.join(matched_folder, f"{manifest_id}.json")
        with open(canvas_json_path, "r", encoding="utf-8") as f:
            canvas_data = json.load(f)

        for canvas in canvas_data:
            img_file = canvas.get("Image Filename")
            canvas_label = canvas.get("Canvas Label")
            img_path = os.path.join(matched_folder, img_file)

            result = classify_with_clip(img_path)
            if result:
                canvas["CLIP Classification"] = result
                csv_rows.append({
                    "Manifest Label": label,
                    "Manifest URI": manifest_uri,
                    "Category": category,
                    "Canvas Label": canvas_label,
                    "Image Filename": img_file,
                    "Prediction": result["prediction"],
                    **{f"Score {k}": round(v, 4) for k, v in result["scores"].items()}
                })

        updated_metadata.append(item)

    # Save CSV
    df = pd.DataFrame(csv_rows)
    df.to_csv(OUTPUT_CSV, index=False)

    # Save updated metadata
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_metadata, f, indent=4, ensure_ascii=False)

    print(f"\n✅ CLIP classification completed.")
    print(f"📄 Updated: {METADATA_FILE}")
    print(f"📄 CSV saved: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
