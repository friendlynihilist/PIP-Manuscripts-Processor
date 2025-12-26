import os
from pathlib import Path
import cv2

# === CONFIG ===
# Use ORIGINAL images without YOLO annotations drawn on them
images_dir = Path("../../data/derived/layout_input")
labels_dir = Path("../../yolo/runs/detect/full_corpus_detection/labels")
output_base = Path("../../data/processed/cropped")
output_base.mkdir(exist_ok=True)

def yolo_to_bbox(txt_bbox, img_w, img_h):
    x_c, y_c, w, h = txt_bbox
    x_c *= img_w
    y_c *= img_h
    w *= img_w
    h *= img_h
    x_min = int(x_c - w / 2)
    y_min = int(y_c - h / 2)
    x_max = int(x_c + w / 2)
    y_max = int(y_c + h / 2)
    return max(x_min, 0), max(y_min, 0), min(x_max, img_w), min(y_max, img_h)

for label_path in labels_dir.glob("*.txt"):
    image_name = label_path.stem + ".jpg"
    image_path = images_dir / image_name

    if not image_path.exists():
        print(f"⚠️ Immagine mancante per {label_path.name}")
        continue

    image = cv2.imread(str(image_path))
    h, w = image.shape[:2]

    with open(label_path, 'r') as f:
        lines = f.read().strip().split('\n')

    for i, line in enumerate(lines):
        if not line.strip():
            continue
        parts = line.split()
        cls_id = int(parts[0])
        bbox = list(map(float, parts[1:5]))

        x_min, y_min, x_max, y_max = yolo_to_bbox(bbox, w, h)
        crop = image[y_min:y_max, x_min:x_max]

        out_dir = output_base / label_path.stem
        out_dir.mkdir(exist_ok=True)

        out_path = out_dir / f"{label_path.stem}_cls{cls_id}_{i}.jpg"
        cv2.imwrite(str(out_path), crop)

print("✅ Ritaglio completato.")