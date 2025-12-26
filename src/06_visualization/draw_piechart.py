import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties

# === CONFIG ===
csv_file_path = "classified_pages.csv"
output_dir = "visualizations"
fonts_dir = "fonts"
output_image = os.path.join(output_dir, "piecharts_text_vs_diagram.png")

os.makedirs(output_dir, exist_ok=True)

# === Load Specific Lato Fonts ===
font_regular_path = os.path.join(fonts_dir, "Lato-Regular.ttf")
font_bold_path = os.path.join(fonts_dir, "Lato-Bold.ttf")

if not os.path.exists(font_regular_path) or not os.path.exists(font_bold_path):
    raise RuntimeError("⚠️ Font 'Lato-Regular.ttf' o 'Lato-Bold.ttf' mancante nella cartella fonts/")

fm.fontManager.addfont(font_regular_path)
fm.fontManager.addfont(font_bold_path)

# Carica i font properties
font_regular = FontProperties(fname=font_regular_path)
font_bold = FontProperties(fname=font_bold_path)

# Imposta il font di default globalmente (per sicurezza)
mpl.rcParams["font.family"] = font_regular.get_name()
mpl.rcParams["font.sans-serif"] = [font_regular.get_name()]

# === Load Data ===
df = pd.read_csv(csv_file_path)
df = df[df["Category Level 1"].str.strip() == "I. Manuscripts"]
df = df[df["Category Level 2"].notnull() & (df["Category Level 2"].str.strip() != "")]
df = df[df["Predicted_Label"].isin(["text", "diagram_mixed"])]

# === Focus categories ===
focus_categories = ["D. Logic", "B. Pragmatism", "A. Mathematics"]

# === Prepare figure ===
fig, axs = plt.subplots(1, 3, figsize=(12, 4))

for i, cat in enumerate(focus_categories):
    df_cat = df[df["Category Level 2"] == cat]
    counts = df_cat["Predicted_Label"].value_counts()
    text_count = counts.get("text", 0)
    diagram_count = counts.get("diagram_mixed", 0)
    total = text_count + diagram_count

    axs[i].pie(
        [text_count, diagram_count],
        labels=["Text", "Diagram"],
        autopct=lambda p: f'{int(p * total / 100)}',
        colors=["#ff8802", "#5fb9b3"],
        startangle=90,
        textprops={"fontsize": 10, "fontproperties": font_regular}
    )
    axs[i].set_title(cat, fontproperties=font_regular, fontsize=12)

    # Precauzione: forza il font anche su tick (anche se pie non li ha)
    for label in axs[i].get_xticklabels() + axs[i].get_yticklabels():
        label.set_fontproperties(font_regular)

plt.tight_layout(rect=[0, 0.03, 1, 0.90])
plt.savefig(output_image, dpi=300)
print(f"✅ Pie charts saved to: {output_image}")
plt.show()