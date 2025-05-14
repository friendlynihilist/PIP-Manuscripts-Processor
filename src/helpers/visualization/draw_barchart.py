import json
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties

# === CONFIG ===
json_file_path = "collection_metadata.json"
output_dir = "./"  # Change if needed

# === Load Custom Font (Lato) ===
fonts_dir = os.path.join(os.getcwd(), "fonts")
if not os.path.isdir(fonts_dir):
    raise RuntimeError(f"Cartella dei font non trovata: {fonts_dir}")
# Aggiungi tutti i .ttf in fonts/ al FontManager
for fname in os.listdir(fonts_dir):
    if fname.lower().endswith('.ttf'):
        fm.fontManager.addfont(os.path.join(fonts_dir, fname))
# Ottieni varianti Lato disponibili
all_fonts = [f.name for f in fm.fontManager.ttflist]
lato_variants = sorted({name for name in all_fonts if 'lato' in name.lower()})
if not lato_variants:
    raise RuntimeError("Nessuna variante di Lato caricata: controlla i .ttf in fonts/")
# Scegli la variante desiderata (es. la prima)
chosen_font = lato_variants[0]
print(f"Usando font: {chosen_font}")
# Imposta Lato come font di default
mpl.rcParams['font.family'] = chosen_font

# === Load JSON ===
with open(json_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# === Convert to DataFrame ===
df = pd.DataFrame(data)

# === Filter for manuscripts only ===
df_manuscripts = df[df["Category Level 1"].str.strip() == "I. Manuscripts"]
# Remove empty Level 2
mask = df_manuscripts["Category Level 2"].notnull() & (df_manuscripts["Category Level 2"].str.strip() != "")
df_manuscripts = df_manuscripts[mask]

# === Count total & digitized items per category ===
total_counts = df_manuscripts["Category Level 2"].value_counts().sort_index()
df_digital = df_manuscripts[df_manuscripts["Digital Link"].notnull() & (df_manuscripts["Digital Link"].str.strip() != "")]
digital_counts = df_digital["Category Level 2"].value_counts().sort_index()

# === Combine counts ===
combined_counts = pd.DataFrame({
    "Total Items": total_counts,
    "Digitized Items": digital_counts
}).fillna(0).astype(int)

# === Export CSV ===
csv_output_path = os.path.join(output_dir, "category_distribution.csv")
combined_counts.to_csv(csv_output_path)
print(f"✅ CSV salvato in: {csv_output_path}")

# === Plotting ===
fig, ax = plt.subplots(figsize=(12, 6))
bar_width = 0.4
x = range(len(combined_counts))

# Bars
ax.bar(x, combined_counts["Total Items"], width=bar_width, label="Total Items")
ax.bar([i + bar_width for i in x], combined_counts["Digitized Items"], width=bar_width, label="Digitized Items")

# FontProperties per Lato
prop = FontProperties(family=chosen_font)

# Annotations
for i in x:
    ax.text(i, combined_counts["Total Items"].iloc[i] + 1,
            str(combined_counts["Total Items"].iloc[i]),
            ha='center', fontproperties=prop, fontsize=8)
    ax.text(i + bar_width, combined_counts["Digitized Items"].iloc[i] + 1,
            str(combined_counts["Digitized Items"].iloc[i]),
            ha='center', fontproperties=prop, fontsize=8)

# Axis setup
ax.set_xticks([i + bar_width / 2 for i in x])
ax.set_xticklabels(combined_counts.index, rotation=45, ha="right", fontproperties=prop)
ax.set_title("Distribution of Manuscripts and Digitized Items by Category (Level 2)", fontproperties=prop, fontsize=14)
ax.set_xlabel("Category", fontproperties=prop)
ax.set_ylabel("Number of Items", fontproperties=prop)
ax.legend(prop=prop)
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()

# === Save image at 300 dpi ===
image_output_path = os.path.join(output_dir, "category_distribution.png")
plt.savefig(image_output_path, dpi=300)
print(f"🖼️ Image salvata in: {image_output_path} (300 dpi)")

plt.show()