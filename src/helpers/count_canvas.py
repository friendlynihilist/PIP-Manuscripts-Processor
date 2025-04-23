import json
import re

# Load both JSON files
with open("collection_metadata.json", "r", encoding="utf-8") as f:
    collection_data = json.load(f)

with open("metadata_with_predictions.json", "r", encoding="utf-8") as f:
    predictions_data = json.load(f)

# Build lookup dictionary for predictions by Manifest URI
predictions_lookup = {entry["Manifest URI"]: entry for entry in predictions_data}

# Function to count pages from canvas labels
def count_pages(canvas_list):
    count = 0
    for canvas in canvas_list:
        label = canvas.get("Canvas Label", "")
        if re.search(r"\[pp?\.\s*\d+\s*[-–]\s*\d+\]", label):
            count += 2
        else:
            count += 1
    return count

# Update collection_metadata.json
collection_updated = []
for item in collection_data:
    manifest_uri = item.get("Manifest URI", "").strip()
    if manifest_uri in predictions_lookup:
        prediction_entry = predictions_lookup[manifest_uri]
        canvas_predictions = prediction_entry.get("Canvas Predictions", [])

        # Update with cleaned canvas data
        canvas_clean = [
            {
                "Label": c.get("Canvas Label", ""),
                "Filename": c.get("Image Filename", "")
            }
            for c in canvas_predictions
        ]

        item["Canvas"] = canvas_clean
        item["Page Count"] = count_pages(canvas_predictions)

    collection_updated.append(item)

# Update metadata_with_predictions.json by adding the Title
for pred_item in predictions_data:
    manifest_uri = pred_item.get("Manifest URI", "").strip()
    matching_item = next((x for x in collection_data if x.get("Manifest URI", "") == manifest_uri), None)
    if matching_item:
        pred_item["Title"] = matching_item.get("Title", "")

# Save updated files
with open("collection_metadata_enriched.json", "w", encoding="utf-8") as f:
    json.dump(collection_updated, f, indent=2, ensure_ascii=False)

with open("metadata_with_predictions_enriched.json", "w", encoding="utf-8") as f:
    json.dump(predictions_data, f, indent=2, ensure_ascii=False)

print("✅ Done. Two enriched files created:")
print(" → collection_metadata_enriched.json")
print(" → metadata_with_predictions_enriched.json")
