import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import os

# === CONFIG ===
train_csv = "../../data/raw/train.csv"
test_csv = "../../data/raw/test.csv"
X_train_path = "../../data/processed/X_train_clip.npy"
X_test_path = "../../data/processed/X_test_clip.npy"

# === LOAD DATA ===
X_train = np.load(X_train_path)
X_test = np.load(X_test_path)

df_train = pd.read_csv(train_csv)
df_test = pd.read_csv(test_csv)

# === ENCODE LABELS ===
le = LabelEncoder()
y_train = le.fit_transform(df_train["Label"])
y_test = le.transform(df_test["Label"])

# === FIT LOGISTIC REGRESSION ===
model = LogisticRegression(C=1.0, max_iter=1000)
model.fit(X_train, y_train)

# === PREDICT AND EVALUATE ===
y_train_pred = model.predict(X_train)
y_test_pred = model.predict(X_test)

print("\n📊 Performance su TRAIN:")
print(classification_report(y_train, y_train_pred, target_names=le.classes_))
print(f"Accuracy (train): {accuracy_score(y_train, y_train_pred):.4f}")

print("\n📊 Performance su TEST:")
print(classification_report(y_test, y_test_pred, target_names=le.classes_))
print(f"Accuracy (test): {accuracy_score(y_test, y_test_pred):.4f}")