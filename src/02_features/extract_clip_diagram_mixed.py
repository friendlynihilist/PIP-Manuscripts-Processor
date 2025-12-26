import os
import numpy as np
import pandas as pd
from PIL import Image
import torch
import open_clip
from clip_utils import get_clip_model

# === CONFIG ===
csv_path = "../../data/results/classified_pages.csv"
output_dir = "../../data/processed/diagram_clip/"
os.makedirs(output_dir, exist_ok=True)

# === Load classified CSV and filter ===
df = pd.read_csv(csv_path)
diagram_df = df[df["Predicted_Label"] == "diagram_mixed"].reset_index(drop=True)

# === Load CLIP model ===
# Use shared CLIP utilities to ensure consistency across pipeline
model, device, preprocess = get_clip_model()

# === Extract embeddings ===
embeddings = []
valid_rows = []

for _, row in diagram_df.iterrows():
    path = row["Path"]
    try:
        image = Image.open(path).convert("RGB")
        input_tensor = preprocess(image).unsqueeze(0).to(device)

        with torch.no_grad():
            emb = model.encode_image(input_tensor).cpu().numpy().flatten()
        embeddings.append(emb)
        valid_rows.append(row)

    except Exception as e:
        print(f"❌ Failed to process {path}: {e}")

# === Save outputs ===
embeddings = np.array(embeddings)
np.save(os.path.join(output_dir, "X_clip_diagram.npy"), embeddings)

pd.DataFrame(valid_rows).to_csv(os.path.join(output_dir, "diagram_clip_index.csv"), index=False)

print(f"✅ Saved {embeddings.shape[0]} CLIP embeddings to: {output_dir}")