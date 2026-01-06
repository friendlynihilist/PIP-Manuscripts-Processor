import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import re
import os
import numpy as np

# --- CONFIG ---
json_file_path = "collection_metadata.json"
output_image = "streamgraph_pagecount_4yr.png"
output_csv = "streamgraph_data_4yr.csv"

# --- Font Setup ---
fonts_dir = os.path.join(os.getcwd(), "fonts")
if not os.path.isdir(fonts_dir):
    raise RuntimeError(f"Cartella dei font non trovata: {fonts_dir}")
for fname in os.listdir(fonts_dir):
    if fname.lower().endswith('.ttf'):
        fm.fontManager.addfont(os.path.join(fonts_dir, fname))
all_fonts = [f.name for f in fm.fontManager.ttflist]
lato_variants = sorted({name for name in all_fonts if 'lato' in name.lower()})
if not lato_variants:
    raise RuntimeError("Nessuna variante di Lato caricata.")
chosen_font = lato_variants[0]
print(f"Usando font: {chosen_font}")
mpl.rcParams['font.family'] = chosen_font

# --- Load JSON ---
with open(json_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# --- Estrai anno e normalizza ---
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
        interval_start = 1834 + ((year - 1834) // 4) * 4
        filtered_data.append({
            "Interval Start": interval_start,
            "Category": category,
            "Pages": pages
        })

df = pd.DataFrame(filtered_data)

# --- Costruisci tutti gli intervalli da 1834 a 1914 ogni 4 anni ---
all_intervals = list(range(1834, 1915, 4))

pivot = df.pivot_table(
    index="Category",
    columns="Interval Start",
    values="Pages",
    aggfunc="sum",
    fill_value=0
)

# Aggiungi intervalli mancanti con 0
for col in all_intervals:
    if col not in pivot.columns:
        pivot[col] = 0
pivot = pivot[sorted(pivot.columns)]

# Salva CSV
pivot.to_csv(output_csv)
print(f"✅ Dati salvati in: {output_csv}")

# --- Streamgraph ---
fig, ax = plt.subplots(figsize=(14, 8))

intervals = all_intervals
categories = pivot.index.tolist()
data = pivot.values

colors = plt.get_cmap("tab20")(np.linspace(0, 1, len(categories)))

ax.stackplot(intervals, data, labels=categories, colors=colors)

ax.set_title("Streamgraph of Digitized Pages by Category and 4-Year Interval (1834–1914)",
             fontsize=16, fontname=chosen_font)
ax.set_xlabel("Interval Start Year", fontsize=12, fontname=chosen_font)
ax.set_ylabel("Page Count", fontsize=12, fontname=chosen_font)

ax.set_xticks(intervals)
ax.set_xlim(min(intervals), max(intervals))
ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=9, title="Category", title_fontsize=10)

plt.tight_layout()
plt.savefig(output_image, dpi=300)
print(f"✅ Streamgraph salvata come: {output_image} (300 dpi)")