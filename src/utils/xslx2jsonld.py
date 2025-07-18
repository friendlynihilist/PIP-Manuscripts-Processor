import pandas as pd
import json

# === CONFIGURAZIONE ===
EXCEL_PATH = "Diagrams.xlsx"
OUTPUT_JSON = "diagrams.json"

# === CARICAMENTO FILE ===
xls = pd.ExcelFile(EXCEL_PATH)
df_diagrams = xls.parse("Diagrams")
df_evaluation = xls.parse("Evaluation")

# === PULIZIA ===
df_diagrams.dropna(how="all", axis=1, inplace=True)
df_evaluation.dropna(how="all", axis=1, inplace=True)

# === COSTRUZIONE OGGETTI JSON ===
output = {}

for _, row in df_diagrams.iterrows():
    diagram_id = str(row["ID Diagram"]).strip()
    
    # Crea dizionario con i metadati
    diagram_data = {}
    for col in df_diagrams.columns:
        if col != "ID Diagram":
            diagram_data[col] = row[col]

    # Cerca le valutazioni associate
    evaluations = []
    matching = df_evaluation[df_evaluation["ID Diagram"].astype(str).str.strip() == diagram_id]
    for _, eval_row in matching.iterrows():
        evaluation = {
            "model": eval_row["Model"],
            "answers": {}
        }
        for col in df_evaluation.columns:
            if col not in ["ID Diagram", "Model"]:
                evaluation["answers"][col] = eval_row[col]
        evaluations.append(evaluation)

    # Aggiungi tutto all'oggetto principale
    output[diagram_id] = {
        "metadata": diagram_data,
        "evaluations": evaluations
    }

# === SALVATAGGIO ===
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ File JSON creato: {OUTPUT_JSON}")