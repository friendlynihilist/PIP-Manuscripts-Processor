# process_peirce_csv.py

import csv
import json
import requests

CSV_PATH = "collection_6437.csv"
JSON_OUTPUT = "peirce_collection_metadata_with_manifest.json"

SKIP_ROWS = 6
HEADERS = [
    "Database Number", "Component Title", "Component Date", "Start Year", "End Year",
    "Component identifier", "Container info", "Component type", "Component creator",
    "Digital Link", "Access Note", "Physical description",
    "Level 1", "Level 2", "Level 3"
]

def clean_manifest_url(url):
    if "/view/" in url:
        base, _, tail = url.partition("/view/")
        tail = tail.split("?")[0].split("$")[0]
        return base + "/" + tail
    return url

def resolve_redirect(url):
    try:
        response = requests.get(url, allow_redirects=True, timeout=10)
        if response.status_code == 200:
            return response.url
    except Exception as e:
        print(f"❌ Redirect error: {url} → {e}")
    return None

def parse_csv_with_manifest(csv_path):
    items = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, fieldnames=HEADERS)
        for _ in range(SKIP_ROWS): next(reader)

        for i, row in enumerate(reader, start=1):
            try:
                item = {k: (v.strip() if v else "") for k, v in row.items()}
                link = item.get("Digital Link", "")
                if link:
                    resolved = resolve_redirect(link)
                    if resolved:
                        item["Viewer URI"] = resolved
                        item["Manifest URI"] = clean_manifest_url(resolved)
                items.append(item)
            except Exception as e:
                print(f"⚠️ Error at row {i}: {e}")
    return items

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    print("🔄 Parsing CSV and resolving manifest links...")
    records = parse_csv_with_manifest(CSV_PATH)
    save_json(records, JSON_OUTPUT)
    print(f"✅ Done. Saved {len(records)} records to {JSON_OUTPUT}")
