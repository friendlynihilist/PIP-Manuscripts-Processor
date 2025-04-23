import json
import requests
import time

# --- CONFIG ---
json_file_path = "collection_metadata.json"
output_file_path = "collection_metadata_updated.json"
timeout = 10  # seconds
delay = 0.5   # seconds between requests

# --- FUNCTIONS ---

def fetch_manifest(manifest_uri):
    try:
        response = requests.get(manifest_uri, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch {manifest_uri}: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error fetching {manifest_uri}: {e}")
    return None

def extract_canvas_data(manifest_data):
    canvas_list = []
    canvases = manifest_data.get("sequences", [])[0].get("canvases", [])
    for i, canvas in enumerate(canvases):
        label = canvas.get("label", f"(seq. {i+1})")
        filename = f"seq{i+1}.jpg"
        canvas_list.append({"Label": label, "Filename": filename})
    return canvas_list

def update_items_with_canvas(data):
    updated = 0
    for item in data:
        if item.get("Page Count", 0) == 0 and "Manifest URI" in item:
            manifest_uri = item["Manifest URI"]
            print(f"🔍 Fetching manifest for: {manifest_uri}")
            manifest_data = fetch_manifest(manifest_uri)
            if not manifest_data:
                continue

            canvas_data = extract_canvas_data(manifest_data)
            item["Canvas"] = canvas_data
            item["Page Count"] = count_canvas_pages(canvas_data)
            updated += 1
            time.sleep(delay)
    print(f"✅ Updated {updated} items.")
    return data

def count_canvas_pages(canvas_data):
    count = 0
    for canvas in canvas_data:
        label = canvas.get("Label", "").lower()
        if "pp." in label:
            # Look for a range like pp. 2–3
            range_match = re.findall(r"pp?\.\s*(\d+)[–-](\d+)", label)
            if range_match:
                start, end = map(int, range_match[0])
                count += (end - start + 1)
            else:
                count += 2
        else:
            count += 1
    return count

# --- MAIN ---

if __name__ == "__main__":
    import re

    with open(json_file_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    updated_data = update_items_with_canvas(metadata)

    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

    print(f"📁 Saved updated metadata to {output_file_path}")
