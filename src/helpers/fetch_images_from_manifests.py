import os
import json
import requests
import re
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# === CONFIG ===
json_file = "collection_metadata.json"
output_dir = "Manuscripts"
log_file = "download_log.txt"
max_workers = 8  # Adjust based on your internet speed and CPU (8-12 is usually safe)

# === HELPERS ===
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def download_image(session, url, path):
    try:
        if os.path.exists(path):
            return True
        response = session.get(url, timeout=30)
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"❌ Failed to fetch {url}: {e}\n")
        return False

def download_manifest(session, url, path):
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"❌ Failed to fetch manifest {url}: {e}\n")
        return False

# === MAIN ===
with open(json_file, "r", encoding="utf-8") as f:
    items = json.load(f)

manuscripts = [item for item in items if item.get("Category Level 1") == "I. Manuscripts" and item.get("Manifest URI") and item.get("Page Count")]

print(f"🔎 Found {len(manuscripts)} Manuscripts to process.")

session = requests.Session()

for item in tqdm(manuscripts, desc="Processing Manuscripts"):
    category1 = sanitize_filename(item["Category Level 1"])
    category2 = sanitize_filename(item["Category Level 2"])
    item_id = sanitize_filename(item["ID"])
    manifest_uri = item["Manifest URI"]

    item_dir = os.path.join(output_dir, category1, category2, item_id)
    os.makedirs(item_dir, exist_ok=True)

    manifest_path = os.path.join(item_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        if not download_manifest(session, manifest_uri, manifest_path):
            continue

    # Read manifest
    try:
        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest = json.load(mf)
        canvases = manifest.get("sequences", [{}])[0].get("canvases", [])
    except Exception as e:
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"❌ Failed to parse manifest for {item_id}: {e}\n")
        continue

    # Prepare download tasks
    tasks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, canvas in enumerate(canvases, start=1):
            image_info = canvas["images"][0]["resource"]["service"]["@id"]
            image_url = f"{image_info}/full/full/0/default.jpg"
            filename = f"seq{idx}.jpg"
            image_path = os.path.join(item_dir, filename)

            tasks.append(executor.submit(download_image, session, image_url, image_path))

        # Wait for downloads to finish
        for task in as_completed(tasks):
            task.result()

print("✅ Done.")
