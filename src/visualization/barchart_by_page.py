import json
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties

# === CONFIG ===
json_file_path = "collection_metadata.json"
output_dir = "./"  # Cambia se necessario

# === Caricamento Font Lato ===
fonts_dir = os.path.join(os.getcwd(), "fonts")
if not os.path.isdir(fonts_dir):
    raise RuntimeError(f"Cartella dei font non trovata: {fonts_dir}")
# Aggiungi tutti i .ttf in fonts/ al FontManager
for fname in os.listdir(fonts_dir):
    if fname.lower().endswith('.ttf'):
        fm.fontManager.addfont(os.path.join(fonts_dir, fname))
# Trova le varianti di Lato disponibili
all_fonts = [f.name for f in fm.fontManager.ttflist]
lato_variants = sorted({name for name in all_fonts if 'lato' in name.lower()})
if not lato_variants:
    raise RuntimeError("Nessuna variante di Lato caricata: controlla i .ttf in fonts/")
# Seleziona la variante desiderata
chosen_font = lato_variants[0]
print(f"Usando font: {chosen_font}")
# Imposta Lato come font di default
mpl.rcParams['font.family'] = chosen_font

# === Caricamento Dati JSON ===
with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.DataFrame(data)
# Filtra solo Manuscripts
df = df[df.get("Category Level 1", '').str.strip() == 'I. Manuscripts']
# Rimuovi categorie di livello 2 vuote
df = df[df.get("Category Level 2").notnull() & (df.get("Category Level 2").str.strip() != '')]
# Assicura che Page Count sia numerico
df['Page Count'] = pd.to_numeric(df['Page Count'], errors='coerce').fillna(0).astype(int)

# === Calcolo Pagine totali per categoria ===
pages_by_cat = df.groupby('Category Level 2')['Page Count'].sum().sort_index()

# === Esporta CSV ===
csv_path = os.path.join(output_dir, 'pages_distribution.csv')
pages_by_cat.to_frame(name='Total Pages').to_csv(csv_path)
print(f"✅ CSV salvato in: {csv_path}")

# === Plot ===
fig, ax = plt.subplots(figsize=(12, 6))
x = range(len(pages_by_cat))
# Barre singole per total pages
ax.bar(x, pages_by_cat.values)

# FontProperties per Lato
prop = FontProperties(family=chosen_font)

# Annotazioni valori sulle barre
for i, val in enumerate(pages_by_cat.values):
    ax.text(i, val + 1, str(val), ha='center', fontproperties=prop, fontsize=8)

# Configurazione assi e titoli
ax.set_xticks(x)
ax.set_xticklabels(pages_by_cat.index, rotation=45, ha='right', fontproperties=prop)
ax.set_title('Page Count Distribution by Category (Level 2)', fontproperties=prop, fontsize=14)
ax.set_xlabel('Category', fontproperties=prop)
ax.set_ylabel('Pages', fontproperties=prop)
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()

# === Salva figura a 300 dpi ===
image_path = os.path.join(output_dir, 'pages_distribution.png')
plt.savefig(image_path, dpi=300)
print(f"🖼️ Immagine salvata in: {image_path} (300 dpi)")

plt.show()