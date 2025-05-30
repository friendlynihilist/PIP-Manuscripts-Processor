import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties

# === CONFIG ===
csv_file_path = "../../data/results/classified_pages.csv"  # Update if needed
output_dir = "../../data/visualizations"
fonts_dir = "../utils/fonts"  # <- updated path
output_image = os.path.join(output_dir, "diagram_distribution_by_category.png")

os.makedirs(output_dir, exist_ok=True)

# === Load Lato Font ===
for fname in os.listdir(fonts_dir):
    if fname.lower().endswith(".ttf"):
        fm.fontManager.addfont(os.path.join(fonts_dir, fname))
all_fonts = [f.name for f in fm.fontManager.ttflist]
lato_variants = sorted({name for name in all_fonts if "lato" in name.lower()})
chosen_font = lato_variants[0] if lato_variants else "DejaVu Sans"
mpl.rcParams["font.family"] = chosen_font
prop = FontProperties(family=chosen_font)

# === Load classified data ===
df = pd.read_csv(csv_file_path)

# Filter only diagram_mixed predictions under Manuscripts
df = df[df["Predicted_Label"] == "diagram_mixed"]
df = df[df["Category Level 1"].str.strip() == "I. Manuscripts"]
df = df[df["Category Level 2"].notnull() & (df["Category Level 2"].str.strip() != "")]

# === Count diagrams by category ===
counts = df.groupby("Category Level 2").size().sort_index()

# === Plot ===
fig, ax = plt.subplots(figsize=(12, 6))
x = range(len(counts))
ax.bar(x, counts.values, color="#336699")

# Annotate bars
for i, val in enumerate(counts.values):
    ax.text(i, val + 0.5, str(val), ha="center", fontproperties=prop, fontsize=8)

# Axis formatting
ax.set_xticks(x)
ax.set_xticklabels(counts.index, rotation=45, ha="right", fontproperties=prop)
ax.set_title("Distribution of Diagram-Mixed Pages by Category (Robin Level 2)", fontproperties=prop, fontsize=14)
ax.set_xlabel("Category", fontproperties=prop)
ax.set_ylabel("Diagram Pages", fontproperties=prop)
ax.grid(axis="y", linestyle="--", alpha=0.5)

plt.tight_layout()

# Save image at 300 dpi
plt.savefig(output_image, dpi=300)
print(f"✅ Plot saved to: {output_image}")

plt.show()