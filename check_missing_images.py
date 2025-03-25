import os
import json
import requests

# 👉 Change this to your local "Manuscripts" folder
BASE_PATH = "Manuscripts"
MISSING_REPORT = "missing_images_report.json"
LOG_SUCCESS = "recovered_images_log.json"
LOG_FAILED = "failed_images_log.json"

# Storage
recovered = []
failed = []

# Load missing images report
with open(MISSING_REPORT, "r", encoding="utf-8") as f:
    missing_images = json.load(f)

# Download loop
for entry in missing_images:
    url = entry["Image URL"]
    save_path = entry["Expected Path"]
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    try:
        print(f"🔄 Downloading {entry['Missing File']}...")
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"✅ Saved to {save_path}")
            recovered.append(entry)
        else:
            print(f"❌ Failed: {response.status_code} for {url}")
            failed.append({**entry, "Status Code": response.status_code})
    except Exception as e:
        print(f"⚠️ Error downloading {url}: {e}")
        failed.append({**entry, "Error": str(e)})

# Write logs
with open(LOG_SUCCESS, "w", encoding="utf-8") as f:
    json.dump(recovered, f, indent=4, ensure_ascii=False)
with open(LOG_FAILED, "w", encoding="utf-8") as f:
    json.dump(failed, f, indent=4, ensure_ascii=False)

print(f"\n✅ Recovery complete.")
print(f"🟢 Recovered: {len(recovered)}")
print(f"🔴 Failed: {len(failed)}")
print(f"📂 Logs written to: {LOG_SUCCESS}, {LOG_FAILED}")
