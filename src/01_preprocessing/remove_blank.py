import pandas as pd
from pathlib import Path

# === CONFIGURAZIONE ===
# Percorso del CSV con metadati
metadata_csv = "data/raw/supervised_annotations.csv"

# Directory delle immagini da cui rimuovere le blank
image_dir = Path("data/derived/layout_input")  # cartella con le immagini YOLO

# === STEP 1: carica il CSV e filtra solo le blank ===
df = pd.read_csv(metadata_csv)
blank_filenames = df[df["Label"] == "blank"]["Filename"].tolist()

# === STEP 2: rimuove i file dalla cartella layout_input con matching parziale ===
all_files = list(image_dir.glob("*.jpg"))
removed = []
skipped = []

for candidate in all_files:
    if any(candidate.name.endswith(f) for f in blank_filenames):
        candidate.unlink()
        removed.append(candidate.name)

# === STEP 3: stampa report ===
print(f"✅ Rimossi {len(removed)} file blank da {image_dir}")
if skipped:
    print(f"⚠️ File non trovati (già rimossi?): {len(skipped)}")
    print(skipped)

# === (Opzionale) salva log in un file ===
with open("removed_blank_pages.txt", "w") as f:
    for name in removed:
        f.write(name + "\n")