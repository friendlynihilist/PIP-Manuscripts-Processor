import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties

# === CONFIG ===
csv_file_path = "../../data/results/classified_pages.csv"
output_dir = "../../data/visualizations"
fonts_dir = "../utils/fonts"
output_image = os.path.join(output_dir, "diagram_vs_text_by_category.png")

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

# === Load Data ===
df = pd.read_csv(csv_file_path)
df = df[df["Category Level 1"].str.strip() == "I. Manuscripts"]
df = df[df["Category Level 2"].notnull() & (df["Category Level 2"].str.strip() != "")]

# Filter only text and diagram_mixed
df = df[df["Predicted_Label"].isin(["text", "diagram_mixed"])]

# === Count by category and label ===
pivot = df.pivot_table(index="Category Level 2", columns="Predicted_Label", aggfunc="size", fill_value=0)
pivot = pivot.sort_index()

# === Plot grouped bars ===
fig, ax = plt.subplots(figsize=(14, 6))
x = range(len(pivot))
bar_width = 0.4

bars1 = ax.bar([i - bar_width/2 for i in x], pivot["text"], width=bar_width, label="Text")
bars2 = ax.bar([i + bar_width/2 for i in x], pivot["diagram_mixed"], width=bar_width, label="Diagram-Mixed")

# Add annotations
for i, val in enumerate(pivot["text"]):
    ax.text(i - bar_width/2, val + 1, str(val), ha="center", fontproperties=prop, fontsize=8)
for i, val in enumerate(pivot["diagram_mixed"]):
    ax.text(i + bar_width/2, val + 1, str(val), ha="center", fontproperties=prop, fontsize=8)

# Axes config
ax.set_xticks(list(x))
ax.set_xticklabels(pivot.index, rotation=45, ha="right", fontproperties=prop)
ax.set_title("Text vs Diagram-Mixed Page Distribution by Category (Robin Level 2)", fontproperties=prop, fontsize=14)
ax.set_xlabel("Category", fontproperties=prop)
ax.set_ylabel("Page Count", fontproperties=prop)
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.legend(prop=prop)

plt.tight_layout()
plt.savefig(output_image, dpi=300)
print(f"✅ Plot saved to: {output_image}")

plt.show()