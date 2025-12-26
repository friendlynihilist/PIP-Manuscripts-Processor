import json
import pandas as pd
import re
import os

# --- CONFIG ---
json_file_path = "collection_metadata.json"
output_csv = "streamgraph_data.csv"

# --- Estrai anno valido ---
def extract_start_year(record):
    try:
        year = int(record.get("Start Year", ""))
        if 1834 <= year <= 1914:
            return year
    except:
        pass
    date_str = record.get("Date", "")
    matches = re.findall(r"\b(18[3-9]\d|19[0-1]\d)\b", date_str)
    if matches:
        y = int(matches[0])
        if 1834 <= y <= 1914:
            return y
    return None

# --- Carica JSON ---
with open(json_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# --- Filtra e aggrega ---
filtered_data = []
for item in data:
    if item.get("Category Level 1") != "I. Manuscripts":
        continue
    category = item.get("Category Level 2", "").strip()
    pages = item.get("Page Count", 0)
    if not category or pages == 0:
        continue
    year = extract_start_year(item)
    if year is not None:
        interval = 1834 + ((year - 1834) // 4) * 4
        filtered_data.append({
            "Interval": interval,
            "Category": category,
            "Pages": pages
        })

df = pd.DataFrame(filtered_data)

# --- Aggrega per Interval + Category ---
agg = df.groupby(["Interval", "Category"], as_index=False)["Pages"].sum()
agg = agg.sort_values(["Interval", "Category"])

# --- Salva ---
agg.to_csv(output_csv, index=False)
print(f"✅ File CSV generato: {output_csv}")