import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import umap.umap_ as umap
from sklearn.preprocessing import LabelEncoder
import os
import matplotlib as mpl
import matplotlib.font_manager as fm

# === CONFIG ===
embedding_path = "../../data/processed/diagram_clip/X_clip_diagram.npy"
index_csv_path = "../../data/processed/diagram_clip/diagram_clip_index.csv"
output_path = "../../data/visualizations/umap_clip_diagram_robin_categories.png"
fonts_dir = "../utils/fonts"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# === Load and register Lato font ===
for fname in os.listdir(fonts_dir):
    if fname.lower().endswith(".ttf"):
        fm.fontManager.addfont(os.path.join(fonts_dir, fname))

# Find a Lato variant
lato_fonts = sorted({f.name for f in fm.fontManager.ttflist if "lato" in f.name.lower()})
chosen_font = lato_fonts[0] if lato_fonts else "DejaVu Sans"
mpl.rcParams['font.family'] = chosen_font
print(f"✅ Using font: {chosen_font}")

# === Load embeddings and metadata ===
X = np.load(embedding_path)
df = pd.read_csv(index_csv_path)

# === Prepare labels ===
labels = df["Category Level 2"].fillna("Unknown")
le = LabelEncoder()
label_ids = le.fit_transform(labels)
label_names = le.classes_

# === Apply UMAP ===
reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='cosine', random_state=42)
X_umap = reducer.fit_transform(X)

# === Plotting ===
plt.figure(figsize=(12, 8))
sns.set(style="whitegrid")
palette = sns.color_palette("tab10", len(np.unique(labels)))

sns.scatterplot(
    x=X_umap[:, 0],
    y=X_umap[:, 1],
    hue=labels,
    palette=palette,
    s=40,
    alpha=0.8,
    edgecolor="none"
)

plt.title("UMAP projection of CLIP embeddings (pages with diagrams)", fontsize=14)
plt.xlabel("UMAP-1")
plt.ylabel("UMAP-2")
plt.legend(title="Category", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(output_path, dpi=300)

print(f"✅ UMAP saved to: {output_path}")