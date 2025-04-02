import os
import pandas as pd

# === CONFIGURAZIONE ===
SORTED_DIR = "manual_annotation_sorted"
CSV_FILE = "manual_annotation/manual_annotation_corrected.csv"
CSV_OUTPUT = "manual_annotation/manual_annotation_corrected_renamed.csv"

# === CARICA CSV ORIGINALE ===
df = pd.read_csv(CSV_FILE)

# === MAPPA ORIGINALE → NUOVO NOME ===
filename_map = {}

for category in os.listdir(SORTED_DIR):
    category_folder = os.path.join(SORTED_DIR, category)
    if not os.path.isdir(category_folder):
        continue

    # Elenca immagini
    images = [f for f in os.listdir(category_folder) if f.lower().endswith((".jpg", ".png"))]
    images.sort()

    print(f"\n📂 Rinomino la categoria: {category}")

    for i, filename in enumerate(images, 1):
        ext = os.path.splitext(filename)[1].lower()
        new_filename = f"{category}_{i:03}{ext}"
        src_path = os.path.join(category_folder, filename)
        dst_path = os.path.join(category_folder, new_filename)

        if filename != new_filename:
            os.rename(src_path, dst_path)
            print(f"🔁 {filename} → {new_filename}")

        # Aggiorna la mappa
        filename_map[filename] = new_filename

# === AGGIORNA CSV ===
updated_rows = 0
for idx, row in df.iterrows():
    old = row["filename"]
    new = filename_map.get(old)
    if new:
        df.at[idx, "filename"] = new
        updated_rows += 1

# === SALVA NUOVO CSV ===
df.to_csv(CSV_OUTPUT, index=False)
print(f"\n✅ {updated_rows} righe aggiornate nel CSV.")
print(f"📄 Nuovo file salvato in: {CSV_OUTPUT}")
