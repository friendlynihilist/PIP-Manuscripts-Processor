import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# --- CONFIG ---
json_file_path = "collection_metadata.json"
output_image = "heatmap_pagecount.png"
output_csv = "heatmap_data.csv"

# --- Load Data ---
with open(json_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# --- Clean and Filter Data ---
def extract_start_year(record):
    try:
        year = int(record["Start Year"])
        if 1834 <= year <= 1914:
            return year
    except:
        pass

    # Try parsing from the "Date" field
    date_str = record.get("Date", "")
    matches = re.findall(r"\b(18[3-9]\d|19[0-1]\d)\b", date_str)
    if matches:
        return int(matches[0])
    return None

filtered_data = []
for item in data:
    if item.get("Category Level 1") != "I. Manuscripts":
        continue
    category = item.get("Category Level 2", "").strip()
    page_count = item.get("Page Count", 0)
    if not category or page_count == 0:
        continue
    year = extract_start_year(item)
    if year:
        decade = (year // 10) * 10
        filtered_data.append({"Decade": decade, "Category": category, "Pages": page_count})

df = pd.DataFrame(filtered_data)

# --- Pivot Table ---
pivot = df.pivot_table(index="Category", columns="Decade", values="Pages", aggfunc="sum", fill_value=0)

# Remove rows and columns with only zeros
pivot = pivot.loc[(pivot != 0).any(axis=1)]
pivot = pivot.loc[:, (pivot != 0).any(axis=0)]

# --- Save to CSV ---
pivot.to_csv(output_csv)
print(f"✅ Data saved to: {output_csv}")

# --- Heatmap ---
plt.figure(figsize=(12, 8))
sns.set(font_scale=0.9)
ax = sns.heatmap(pivot, annot=True, fmt="d", cmap="YlGnBu", linewidths=0.5, cbar_kws={"label": "Page Count"})

plt.title("Heatmap of Page Counts by Category and Decade (1834–1914)", fontsize=14)
plt.xlabel("Decade")
plt.ylabel("Category")
plt.tight_layout()

plt.savefig(output_image)
print(f"✅ Heatmap saved as: {output_image}")
