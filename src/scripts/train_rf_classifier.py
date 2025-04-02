import os
import glob
import torch
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import joblib
import clip

# CONFIG
DATASET_DIR = "annotated_dataset"
MODEL_OUTPUT = "clip_rf_classifier.pkl"
ENCODER_OUTPUT = "label_encoder.pkl"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load CLIP
print("🔁 Caricamento modello CLIP...")
model, preprocess = clip.load("ViT-B/32", device=DEVICE)

# Load images and labels
image_paths = []
labels = []

print("📂 Caricamento immagini da:", DATASET_DIR)
for label in os.listdir(DATASET_DIR):
    label_path = os.path.join(DATASET_DIR, label)
    if os.path.isdir(label_path):
        for img_file in glob.glob(os.path.join(label_path, "*.jpg")):
            image_paths.append(img_file)
            labels.append(label)

print(f"✅ Trovate {len(image_paths)} immagini in {len(set(labels))} classi")

# Encode labels
le = LabelEncoder()
encoded_labels = le.fit_transform(labels)

# Extract CLIP embeddings
print("🧠 Estrazione delle CLIP embeddings...")
features = []

for img_path in tqdm(image_paths):
    try:
        image = preprocess(Image.open(img_path).convert("RGB")).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            embedding = model.encode_image(image).cpu().numpy().flatten()
        features.append(embedding)
    except Exception as e:
        print(f"❌ Errore con {img_path}: {e}")
        features.append(np.zeros(512))  # fallback

X = np.array(features)
y = np.array(encoded_labels)

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train Classifier
print("🌲 Addestramento classificatore Random Forest...")
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Evaluation
y_pred = clf.predict(X_test)

# Filtra solo le classi presenti nel test set
present_labels = np.unique(y_test)
target_names = le.inverse_transform(present_labels)

# === REPORT TESTUALE ===
report_text = classification_report(
    y_test, y_pred,
    labels=present_labels,
    target_names=target_names,
    zero_division=0
)

print("\n📊 Classification Report:")
print(report_text)

with open("classification_report.txt", "w") as f:
    f.write(report_text)

# === CONFUSION MATRIX CSV ===
cm = confusion_matrix(y_test, y_pred, labels=present_labels)
cm_df = pd.DataFrame(cm, index=target_names, columns=target_names)
cm_df.to_csv("confusion_matrix.csv")

print("📄 Report salvato come classification_report.txt")
print("🧩 Confusion matrix salvata come confusion_matrix.csv")

# Save model
joblib.dump(clf, MODEL_OUTPUT)
joblib.dump(le, ENCODER_OUTPUT)

print(f"\n✅ Modello salvato come {MODEL_OUTPUT}")
print(f"🎯 Label encoder salvato come {ENCODER_OUTPUT}")
