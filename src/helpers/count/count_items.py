import json

# === Load JSON ===
json_file_path = "collection_metadata.json"

with open(json_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

count = 0        # Total manuscript items
dcount = 0       # Digitized manuscript items
pcount = 0       # Total page count

for item in data:
    series = item.get("Category Level 1") == "I. Manuscripts"
    subseries = item.get("Category Level 2")  # This should be a string
    link = item.get("Digital Link", "")
    page = item.get("Page Count", 0)

    if series and subseries:
        count += 1
    if series and subseries and link:
        dcount += 1
    if series and subseries and isinstance(page, int):
        pcount += page

print(f"Total items (Manuscripts): {count}")
print(f"Total digitized items (Manuscripts): {dcount}")
print(f"Total pages for digitized items (Manuscripts): {pcount}")
