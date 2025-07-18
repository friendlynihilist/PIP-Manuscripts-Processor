import pandas as pd
import json

# Percorsi ai file
json_path = "diagrams.json"
excel_path = "groundtruth.xlsx"
output_path = "diagrams_with_gt.json"

# Carica JSON
with open(json_path, 'r') as f:
    diagrams = json.load(f)

# Carica Excel
df = pd.read_excel(excel_path)

# Normalizza gli ID per matching
df['ID Diagram'] = df['ID Diagram'].str.strip()

# Aggiungi le ground-truth nel JSON
for _, row in df.iterrows():
    diagram_id = row["ID Diagram"]
    if diagram_id in diagrams:
        diagrams[diagram_id]["ground_truth"] = {
            "Morphological Question": row["Morphological Question"],
            "Indexical Question": row["Indexical Question"],
            "Symbolic Question": row["Symbolic Question"],
        }

# Salva il nuovo JSON
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(diagrams, f, indent=2, ensure_ascii=False)

print(f"Ground-truth added and saved to {output_path}")