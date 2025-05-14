import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties
import re
import os

# --- CONFIG ---
json_file_path = "collection_metadata.json"
output_image = "heatmap_pagecount_4yr.png"
output_csv = "heatmap_data_4yr.csv"

# --- Custom Font Loading ---
fonts_dir = os.path.join(os.getcwd(), "fonts")
if not os.path.isdir(fonts_dir):
    raise RuntimeError(f"Cartella dei font non trovata: {fonts_dir}")
# Aggiungi tutti i .ttf in fonts/ al FontManager
for fname in os.listdir(fonts_dir):
    if fname.lower().endswith('.ttf'):
        fm.fontManager.addfont(os.path.join(fonts_dir, fname))
# Ricava le varianti di Lato disponibili
all_fonts = [f.name for f in fm.fontManager.ttflist]
lato_variants = sorted({name for name in all_fonts if 'lato' in name.lower()})
if not lato_variants:
    raise RuntimeError("Nessuna variante di Lato caricata: controlla i .ttf in fonts/")
# Scegli la variante desiderata (es. la prima)
chosen_font = lato_variants[0]
print(f"Usando font: {chosen_font}")
# Imposta il font di default
mpl.rcParams['font.family'] = chosen_font

# --- Load Data ---
with open(json_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# --- Clean and Filter Data ---
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

pivot = df.pivot_table(
    index="Category",
    columns="Interval Start",
    values="Pages",
    aggfunc="sum",
    fill_value=0
)
pivot = pivot.loc[(pivot != 0).any(axis=1)]
pivot = pivot.loc[:, (pivot != 0).any(axis=0)]

pivot.to_csv(output_csv)
print(f"✅ Dati salvati in: {output_csv}")

# --- Heatmap ---
plt.figure(figsize=(12, 8))
sns.set(font_scale=0.9)

ax = sns.heatmap(
    pivot,
    annot=True,
    fmt="d",
    cmap="YlGnBu",
    linewidths=0.5,
    cbar_kws={"label": "Page Count"}
)
# Applica il FontProperties a titolo ed etichette
prop = FontProperties(family=chosen_font)
ax.set_title("Heatmap of Page Counts by Category and 4-Year Interval (1834–1914)", fontproperties=prop, fontsize=14)
ax.set_xlabel("Interval Start Year", fontproperties=prop)
ax.set_ylabel("Category", fontproperties=prop)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontproperties(prop)

plt.tight_layout()
# Save PNG at 300 dpi
plt.savefig(output_image, dpi=300)
print(f"✅ Heatmap salvata come: {output_image} (300 dpi)")
