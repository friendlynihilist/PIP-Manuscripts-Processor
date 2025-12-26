import os
import json
import uuid
from pathlib import Path
from PIL import Image
from datetime import datetime

# === CONFIG ===
yolo_labels_dir = Path("../../yolo/runs/detect/full_corpus_detection/labels")
yolo_images_dir = Path("../../yolo/runs/detect/full_corpus_detection")
collection_metadata_path = Path("../../data/processed/collection_metadata.json")
output_file = Path("yolo_layout_annotations.jsonld")

# YOLO class mapping
CLASS_NAMES = {
    0: "diagram",
    1: "text_block"
}

def yolo_to_pixel_coords(yolo_bbox, img_width, img_height):
    """
    Convert YOLO normalized coordinates to pixel coordinates.

    YOLO format: (center_x, center_y, width, height) - all normalized 0-1
    Returns: (x, y, width, height) in pixels - IIIF xywh format
    """
    cx, cy, w, h = yolo_bbox

    # Convert to pixel coordinates
    cx_px = cx * img_width
    cy_px = cy * img_height
    w_px = w * img_width
    h_px = h * img_height

    # Convert center coords to top-left corner
    x = int(cx_px - w_px / 2)
    y = int(cy_px - h_px / 2)
    width = int(w_px)
    height = int(h_px)

    # Ensure coordinates are within image bounds
    x = max(0, min(x, img_width))
    y = max(0, min(y, img_height))
    width = max(0, min(width, img_width - x))
    height = max(0, min(height, img_height - y))

    return x, y, width, height

def create_annotation(canvas_uri, class_id, class_name, bbox_xywh, index, canvas_label):
    """
    Create a IIIF Web Annotation for a detected region.
    """
    x, y, w, h = bbox_xywh

    annotation = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": f"{canvas_uri}#yolo-{class_name}-{index}",
        "type": "Annotation",
        "motivation": "identifying",
        "created": datetime.now().isoformat(),
        "generator": {
            "id": "https://github.com/ultralytics/ultralytics",
            "type": "Software",
            "name": "YOLOv8 Layout Detection Model",
            "homepage": "https://github.com/ultralytics/ultralytics"
        },
        "body": {
            "type": "TextualBody",
            "value": class_name,
            "purpose": "tagging",
            "format": "text/plain",
            "language": "en"
        },
        "target": {
            "source": canvas_uri,
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": f"xywh={x},{y},{w},{h}"
            }
        }
    }

    return annotation

def get_canvas_uri_from_filename(filename, collection_metadata):
    """
    Map filename to canvas URI using collection metadata.
    Filename format: Category__ManuscriptID__seqN.txt
    """
    # Parse filename
    stem = filename.replace(".txt", "").replace(".jpg", "")
    parts = stem.split("__")

    if len(parts) < 3:
        return None, None

    category = parts[0].replace("_", ". ")  # e.g., "D._Logic" -> "D. Logic"
    manuscript_id = parts[1]
    seq_part = parts[2]  # e.g., "seq613"

    # Find manuscript in collection metadata
    for item in collection_metadata:
        if item.get("ID") == manuscript_id:
            manifest_uri = item.get("Manifest URI", "")

            # Construct canvas URI (Harvard IIIF pattern)
            # This is an approximation - real canvas URIs would come from manifest
            # For now, we'll use a placeholder pattern
            canvas_uri = f"{manifest_uri}/canvas/{stem}"
            canvas_label = f"{category}/{manuscript_id}/{seq_part}"

            return canvas_uri, canvas_label

    return None, None

def process_yolo_detections():
    """
    Process all YOLO detection labels and create IIIF annotations.
    """
    # Load collection metadata
    with open(collection_metadata_path, "r") as f:
        collection_metadata = json.load(f)

    all_annotations = []
    processed_count = 0
    skipped_count = 0

    # Process each label file
    for label_file in sorted(yolo_labels_dir.glob("*.txt")):
        # Get corresponding image to get dimensions
        image_file = yolo_images_dir / f"{label_file.stem}.jpg"

        if not image_file.exists():
            print(f"⚠️  Image not found for {label_file.name}")
            skipped_count += 1
            continue

        # Get canvas URI
        canvas_uri, canvas_label = get_canvas_uri_from_filename(
            label_file.name, collection_metadata
        )

        if not canvas_uri:
            print(f"⚠️  Could not map {label_file.name} to canvas URI")
            skipped_count += 1
            continue

        # Get image dimensions
        try:
            with Image.open(image_file) as img:
                img_width, img_height = img.size
        except Exception as e:
            print(f"❌ Failed to read image {image_file.name}: {e}")
            skipped_count += 1
            continue

        # Read YOLO detections
        detections_by_class = {0: [], 1: []}  # diagram, text_block

        with open(label_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue

                parts = line.strip().split()
                class_id = int(parts[0])
                yolo_bbox = list(map(float, parts[1:5]))

                # Convert to pixel coordinates
                bbox_xywh = yolo_to_pixel_coords(yolo_bbox, img_width, img_height)
                detections_by_class[class_id].append(bbox_xywh)

        # Create annotations for each detection
        page_annotations = []

        for class_id, bboxes in detections_by_class.items():
            class_name = CLASS_NAMES[class_id]

            for idx, bbox_xywh in enumerate(bboxes):
                annotation = create_annotation(
                    canvas_uri=canvas_uri,
                    class_id=class_id,
                    class_name=class_name,
                    bbox_xywh=bbox_xywh,
                    index=idx,
                    canvas_label=canvas_label
                )
                page_annotations.append(annotation)

        all_annotations.extend(page_annotations)
        processed_count += 1

        if processed_count % 100 == 0:
            print(f"✓ Processed {processed_count} pages...")

    # Create annotation collection
    annotation_collection = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": "https://w3id.org/mlao/pip/yolo-layout-annotations",
        "type": "AnnotationCollection",
        "label": "YOLO Layout Detection Annotations for Peirce Manuscripts",
        "created": datetime.now().isoformat(),
        "generator": {
            "id": "https://github.com/ultralytics/ultralytics",
            "type": "Software",
            "name": "YOLOv8 Layout Detection Pipeline"
        },
        "total": len(all_annotations),
        "first": {
            "id": "https://w3id.org/mlao/pip/yolo-layout-annotations/page1",
            "type": "AnnotationPage",
            "items": all_annotations
        }
    }

    # Save to file
    with open(output_file, "w") as f:
        json.dump(annotation_collection, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ IIIF Annotation Generation Complete!")
    print(f"{'='*60}")
    print(f"📄 Processed pages: {processed_count}")
    print(f"⚠️  Skipped pages: {skipped_count}")
    print(f"📊 Total annotations: {len(all_annotations)}")
    print(f"   - Diagrams: {sum(1 for a in all_annotations if 'diagram' in a['id'])}")
    print(f"   - Text blocks: {sum(1 for a in all_annotations if 'text_block' in a['id'])}")
    print(f"💾 Output: {output_file.absolute()}")
    print(f"{'='*60}")

if __name__ == "__main__":
    process_yolo_detections()
