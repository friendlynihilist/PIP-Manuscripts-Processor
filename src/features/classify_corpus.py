import numpy as np
import pandas as pd
import joblib
import pickle

# === Paths ===
embedding_path = "../../data/processed/clip_embeddings_full.npy"
index_csv = "../../data/processed/clip_embedding_index.csv"
model_path = "../../models/logreg_clip_model.pkl"
encoder_path = "../../data/processed/label_encoder.pkl"
output_path = "../../data/results/classified_pages.csv"

# === Load embeddings and metadata ===
X = np.load(embedding_path)
df = pd.read_csv(index_csv)  # Contains Path, ID, Category, etc.

# === Load model and label encoder ===
model = joblib.load(model_path)

with open(encoder_path, "rb") as f:
    le = pickle.load(f)

# === Predict classes ===
y_pred = model.predict(X)
predicted_labels = le.inverse_transform(y_pred)

# === Attach predictions to metadata ===
df["Predicted_Label"] = predicted_labels

# === Save result ===
df.to_csv(output_path, index=False)
print(f"✅ Classified {len(df)} pages and saved to {output_path}")