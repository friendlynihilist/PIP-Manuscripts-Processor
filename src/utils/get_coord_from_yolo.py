import json
from pathlib import Path

# === CONFIG ===
labels_dir = Path("../../yolo/runs/detect/peirce_eval/labels")
images_dir = Path("../../yolo/runs/detect/peirce_eval/images")  # Needed to get image dimensions

# === Output ===
coordinates_map = {}

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
        print(f"⚠️ Missing image for {label_path.name}")
        continue

    # Get image dimensions
    import cv2
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
        x = x_min
        y = y_min
        w_box = x_max - x_min
        h_box = y_max - y_min

        diagram_id = f"{label_path.stem}_cls{cls_id}_{i}"
        coordinates_map[diagram_id] = f"xywh={x},{y},{w_box},{h_box}"

# Save output
with open("diagram_coordinates.json", "w") as f:
    json.dump(coordinates_map, f, indent=2)

print("✅ Coordinates saved to diagram_coordinates.json.")