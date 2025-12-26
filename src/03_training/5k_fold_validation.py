import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix

# === CONFIG ===
X_train_path = "../../data/processed/X_train_clip.npy"
train_csv = "../../data/raw/train.csv"

X = np.load(X_train_path)
df = pd.read_csv(train_csv)
y = df["Label"].values
labels_names = sorted(np.unique(y).tolist())

clf = LogisticRegression(penalty='l2', solver='lbfgs', max_iter=1000, C=1.0, random_state=42)
cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

f1_scores = cross_val_score(clf, X, y, cv=cv, scoring='f1_macro', n_jobs=-1)
acc_scores = cross_val_score(clf, X, y, cv=cv, scoring='accuracy', n_jobs=-1)

print("\n📌 10-fold cross-validation results")
print(f"Accuracy: mean={acc_scores.mean():.3f}, std={acc_scores.std():.3f}")
print(f"F1 macro: mean={f1_scores.mean():.3f}, std={f1_scores.std():.3f}")

reports = []
conf_mats = []

for fold, (train_idx, val_idx) in enumerate(cv.split(X, y), 1):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]

    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_val)

    reports.append(classification_report(y_val, y_pred, target_names=labels_names, output_dict=True))
    conf_mats.append(confusion_matrix(y_val, y_pred, labels=labels_names))

    print(f"\n—— Fold {fold} ——")
    print(classification_report(y_val, y_pred, target_names=labels_names, digits=3))

# === Aggrega confusion matrix e plottala ===
conf_mat_sum = np.sum(conf_mats, axis=0)
conf_mat_norm = conf_mat_sum.astype('float') / conf_mat_sum.sum(axis=1, keepdims=True)

plt.figure(figsize=(8, 6))
sns.heatmap(conf_mat_norm, annot=True, fmt=".2f", xticklabels=labels_names, yticklabels=labels_names, cmap="Blues")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.title("Normalized Confusion Matrix (10-fold)")
plt.tight_layout()
plt.savefig("confusion_matrix_avg.png", dpi=300)
plt.close()

# === Salva CSV delle metriche per fold ===
df_list = []
for i, rep in enumerate(reports, 1):
    df_fold = pd.DataFrame(rep).T.loc[labels_names + ['accuracy', 'macro avg', 'weighted avg']]
    df_fold['fold'] = i
    df_list.append(df_fold)

summary_df = pd.concat(df_list)
summary_df.to_csv("cv_clip_lr_report_10fold.csv", index=True)
np.savez("cv_clip_lr_scores_10fold.npz", acc=acc_scores, f1=f1_scores)

print("✅ Saved confusion_matrix_avg.png and metric report.")