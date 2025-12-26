import os
import numpy as np
import pandas as pd
import pickle
from tqdm import tqdm
from sklearn.preprocessing import LabelEncoder
from PIL import Image

# --- CONFIGURAZIONE ---
train_csv = "train.csv"
test_csv = "test.csv"
output_dir = "preprocessed_data/"  # oppure "preprocessed_data/" se vuoi salvarli in una cartella
img_size = (224, 224)

# --- FUNZIONI ---
def load_images_and_labels(csv_path):
    df = pd.read_csv(csv_path)
    X = []
    y = []
    
    for _, row in tqdm(df.iterrows(), total=len(df)):
        img_path = row["Path"]
        label = row["Label"]
        
        if not os.path.exists(img_path):
            print(f"Missing file: {img_path}")
            continue
        
        try:
            img = Image.open(img_path).convert("RGB")
            img = img.resize(img_size, Image.Resampling.LANCZOS)
            img_array = np.array(img).flatten()  # Flatten
            X.append(img_array)
            y.append(label)
        except Exception as e:
            print(f"Error reading {img_path}: {e}")
    
    return np.array(X), np.array(y)

# --- CARICAMENTO ---
print("Preprocessing training set...")
X_train, y_train = load_images_and_labels(train_csv)

print("Preprocessing test set...")
X_test, y_test = load_images_and_labels(test_csv)

# --- ENCODING LABELS ---
label_encoder = LabelEncoder()
y_train_encoded = label_encoder.fit_transform(y_train)
y_test_encoded = label_encoder.transform(y_test)

# --- SALVATAGGIO ---
np.save(os.path.join(output_dir, "X_train.npy"), X_train)
np.save(os.path.join(output_dir, "y_train.npy"), y_train_encoded)
np.save(os.path.join(output_dir, "X_test.npy"), X_test)
np.save(os.path.join(output_dir, "y_test.npy"), y_test_encoded)

with open(os.path.join(output_dir, "label_encoder.pkl"), "wb") as f:
    pickle.dump(label_encoder, f)

print(f"Train set: {X_train.shape}, {y_train_encoded.shape}")
print(f"Test set: {X_test.shape}, {y_test_encoded.shape}")
print(f"Labels: {list(label_encoder.classes_)}")
