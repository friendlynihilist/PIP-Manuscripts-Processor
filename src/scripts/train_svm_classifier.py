import os
import glob
import numpy as np
from PIL import Image
from tqdm import tqdm
import torch
import clip
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import joblib

# CONFIG
DATASET_DIR = "annotated_dataset"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_OUTPUT = "clip_svm_classifier.pkl"
ENCODER_OUTPUT = "label_encoder.pkl"

# Carica CLIP
print("🔁 Caricamento modello CLIP...")
model, preprocess = clip.load("ViT-B/32", device=DEVICE)

# Carica immagini e label
image_paths = []
labels = []

for label in os.listdir(DATASET_DIR):
    label_path = os.path.join(DATASET_DIR, label)
    if os.path.isdir(label_path):
        for img_file in glob.glob(os.path.join(label_path, "*.jpg")):
            image_paths.append(img_file)
            labels.append(label)

print(f"📂 Trovate {len(image_paths)} immagini.")

# Codifica le etichette
le = LabelEncoder()
encoded_labels = le.fit_transform(labels)

# Estrai le embedding
features = []
print("🧠 Estrazione delle CLIP embedding...")
for img_path in tqdm(image_paths):
    try:
        image = preprocess(Image.open(img_path).convert("RGB")).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            embedding = model.encode_image(image).cpu().numpy().flatten()
        features.append(embedding)
    except Exception as e:
        print(f"❌ Errore con {img_path}: {e}")
        features.append(np.zeros(512))

X = np.array(features)
y = np.array(encoded_labels)

# Train/Test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Addestramento SVM
print("🎯 Addestramento SVM...")
clf = SVC(kernel="linear", probability=True, random_state=42)
clf.fit(X_train, y_train)

# Valutazione
y_pred = clf.predict(X_test)
present_labels = np.unique(y_test)
target_names = le.inverse_transform(present_labels)

report_text = classification_report(
    y_test, y_pred,
    labels=present_labels,
    target_names=target_names,
    zero_division=0
)
print("\n📊 Classification Report (SVM):")
print(report_text)

with open("classification_report_svm.txt", "w") as f:
    f.write(report_text)

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred, labels=present_labels)
cm_df = pd.DataFrame(cm, index=target_names, columns=target_names)
cm_df.to_csv("confusion_matrix_svm.csv")

# Salva il modello
joblib.dump(clf, MODEL_OUTPUT)
joblib.dump(le, ENCODER_OUTPUT)

print(f"\n✅ Modello SVM salvato come {MODEL_OUTPUT}")
print(f"🎯 Report salvato come classification_report_svm.txt")
