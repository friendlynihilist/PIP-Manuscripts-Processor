import os
import shutil
import pandas as pd

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANNOTATION_DIR = os.path.join(BASE_DIR, "manual_annotation")
CSV_PATH = os.path.join(ANNOTATION_DIR, "manual_annotation_corrected.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "manual_annotation_sorted")

# Leggi CSV
df = pd.read_csv(CSV_PATH)

# Crea cartella output
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Itera su ogni riga
for _, row in df.iterrows():
    filename = row["filename"]
    label = str(row["corrected_label"]).strip().lower()
    src_path = os.path.join(ANNOTATION_DIR, row["predicted_label"], filename)
    dst_folder = os.path.join(OUTPUT_DIR, label)
    dst_path = os.path.join(dst_folder, filename)

    if not os.path.exists(src_path):
        print(f"⚠️ Immagine non trovata: {src_path}")
        continue

    os.makedirs(dst_folder, exist_ok=True)
    shutil.copy2(src_path, dst_path)
    print(f"✅ Spostata {filename} → {label}/")

print("\n🎉 Riordino completato. Immagini salvate in:", OUTPUT_DIR)
