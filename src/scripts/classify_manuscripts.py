import os
import json
import cv2
import pytesseract
import pandas as pd
import numpy as np

# ---------- CONFIG ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MANUSCRIPTS_DIR = os.path.join(SCRIPT_DIR, "Manuscripts")
METADATA_FILE = os.path.join(SCRIPT_DIR, "metadata_updated.json")
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "classification_summary.csv")

pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/bin/tesseract"

# ---------- CLASSIFICAZIONE AGGIORNATA ----------
def classify_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None

    # Edge detection
    edges = cv2.Canny(image, 50, 150)
    edge_density = np.sum(edges) / (image.shape[0] * image.shape[1])

    # OCR
    text = pytesseract.image_to_string(image)
    text_length = len(text.strip())

    # Decisione classificazione
    if edge_density > 0.01 and text_length < 50:
        prediction = "diagram"
    elif text_length > 200:
        prediction = "text"
    else:
        prediction = "uncertain"

    return {
        "text_len": text_length,
        "edge_density": edge_density,
        "prediction": prediction
    }

# ---------- MAIN ----------
def main():
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    updated_metadata = []
    csv_rows = []

    for item in metadata:
        category = item["Category"]
        label = item["label"]
        manifest_uri = item["Manifest URI"]
        manifest_id = manifest_uri.split(":")[-1]

        category_path = os.path.join(MANUSCRIPTS_DIR, category)
        if not os.path.exists(category_path):
            continue

        matched_folder = None
        for folder in os.listdir(category_path):
            folder_path = os.path.join(category_path, folder)
            if os.path.isdir(folder_path) and os.path.exists(os.path.join(folder_path, f"{manifest_id}.json")):
                matched_folder = folder_path
                break

        if not matched_folder:
            print(f"[!] Manifest ID {manifest_id} not found in category {category}")
            continue

        canvas_json_path = os.path.join(matched_folder, f"{manifest_id}.json")
        with open(canvas_json_path, "r", encoding="utf-8") as f:
            canvas_data = json.load(f)

        print(f"\n📘 Processing manuscript: {label}")
        classifications = []
        for canvas in canvas_data:
            img_file = canvas.get("Image Filename")
            canvas_label = canvas.get("Canvas Label")
            img_path = os.path.join(matched_folder, img_file)
            result = classify_image(img_path)
            if result:
                print(f"   → {img_file:15} | {canvas_label:20} | prediction: {result['prediction']}")
                classifications.append({
                    "Canvas Label": canvas_label,
                    "Image Filename": img_file,
                    "Prediction": result["prediction"]
                })
                csv_rows.append({
                    "Manifest Label": label,
                    "Manifest URI": manifest_uri,
                    "Category": category,
                    "Canvas Label": canvas_label,
                    "Image Filename": img_file,
                    "Prediction": result["prediction"]
                })
            else:
                print(f"   → {img_file:15} | [ERROR] Image not found or unreadable.")

        item["Canvas Classifications"] = classifications
        updated_metadata.append(item)

    # Save updated metadata
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_metadata, f, indent=4, ensure_ascii=False)

    # Save CSV summary
    df = pd.DataFrame(csv_rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Classificazione completata.")
    print(f"📄 File aggiornato: {METADATA_FILE}")
    print(f"📄 CSV generato: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
