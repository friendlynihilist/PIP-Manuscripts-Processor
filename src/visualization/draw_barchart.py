import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties

# === CONFIG ===
json_file_path = "../../data/processed/collection_metadata.json"
output_dir = "../../data/visualizations"
fonts_dir = "../utils/fonts"
os.makedirs(output_dir, exist_ok=True)

# === Load Lato Font ===
if not os.path.isdir(fonts_dir):
    raise RuntimeError(f"Font directory not found: {fonts_dir}")

for fname in os.listdir(fonts_dir):
    if fname.lower().endswith(".ttf"):
        fm.fontManager.addfont(os.path.join(fonts_dir, fname))

all_fonts = [f.name for f in fm.fontManager.ttflist]
lato_variants = sorted({name for name in all_fonts if "lato" in name.lower()})
if not lato_variants:
    raise RuntimeError("No Lato font variant loaded. Check .ttf files in fonts/")

chosen_font = lato_variants[0]
prop = FontProperties(family=chosen_font)
mpl.rcParams["font.family"] = chosen_font
print(f"✅ Using font: {chosen_font}")

# === Load JSON ===
with open(json_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# === Filter for Manuscripts only ===
df_manuscripts = df[df["Category Level 1"].str.strip() == "I. Manuscripts"]
df_manuscripts = df_manuscripts[
    df_manuscripts["Category Level 2"].notnull() &
    (df_manuscripts["Category Level 2"].str.strip() != "")
]

# === Count totals and digitized ===
total_counts = df_manuscripts["Category Level 2"].value_counts().sort_index()
df_digital = df_manuscripts[
    df_manuscripts["Digital Link"].notnull() &
    (df_manuscripts["Digital Link"].str.strip() != "")
]
digital_counts = df_digital["Category Level 2"].value_counts().sort_index()

# === Combine ===
combined_counts = pd.DataFrame({
    "Total Items": total_counts,
    "Digitized Items": digital_counts
}).fillna(0).astype(int)

# === Export CSV ===
csv_output_path = os.path.join(output_dir, "category_distribution.csv")
combined_counts.to_csv(csv_output_path)
print(f"✅ CSV saved to: {csv_output_path}")

# === Plot ===
fig, ax = plt.subplots(figsize=(12, 6))
bar_width = 0.4
x = range(len(combined_counts))

ax.bar(x, combined_counts["Total Items"], width=bar_width, label="Total Items", color="#4063D8")
ax.bar([i + bar_width for i in x], combined_counts["Digitized Items"], width=bar_width, label="Digitized Items", color="#389826")

# Annotate values
for i in x:
    ax.text(i, combined_counts["Total Items"].iloc[i] + 0.5,
            str(combined_counts["Total Items"].iloc[i]),
            ha='center', fontproperties=prop, fontsize=8)
    ax.text(i + bar_width, combined_counts["Digitized Items"].iloc[i] + 0.5,
            str(combined_counts["Digitized Items"].iloc[i]),
            ha='center', fontproperties=prop, fontsize=8)

# Labels and styles
ax.set_xticks([i + bar_width / 2 for i in x])
ax.set_xticklabels(combined_counts.index, rotation=45, ha="right", fontproperties=prop)
ax.set_title("Distribution of Manuscripts and Digitized Items by Category (Level 2)", fontproperties=prop, fontsize=14)
ax.set_xlabel("Category", fontproperties=prop)
ax.set_ylabel("Number of Items", fontproperties=prop)
ax.legend(prop=prop)
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()

# === Save 300 dpi image ===
image_output_path = os.path.join(output_dir, "category_distribution.png")
plt.savefig(image_output_path, dpi=300)
print(f"🖼️ Image saved to: {image_output_path} (300 dpi)")

plt.show()