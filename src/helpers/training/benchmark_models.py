import numpy as np
import os
import pandas as pd
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from tqdm import tqdm

# === CONFIG ===
features = ["hog", "cnn", "clip"]
models = {
    "Linear SVM": SVC(kernel="linear", C=1.0, random_state=42),
    "SVM RBF": SVC(kernel="rbf", C=1.0, gamma="scale", random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "k-NN (k=5)": KNeighborsClassifier(n_neighbors=5)
}
feature_dir = "preprocessed_data"
results_dir = "results"
summary_file = os.path.join(results_dir, "benchmark_summary.csv")
os.makedirs(results_dir, exist_ok=True)

# === INIT RESULTS ===
all_results = []

# === LOOP ===
for feat in features:
    print(f"\n📦 Loading features: {feat.upper()}")

    try:
        X_train = np.load(os.path.join(feature_dir, f"X_train_{feat}.npy"))
        y_train = np.load(os.path.join(feature_dir, f"y_train.npy"))
        X_test = np.load(os.path.join(feature_dir, f"X_test_{feat}.npy"))
        y_test = np.load(os.path.join(feature_dir, f"y_test.npy"))
    except FileNotFoundError as e:
        print(f"❌ Missing files for {feat}: {e}")
        continue

    print(f"🔢 Train samples: {len(X_train)} | Test samples: {len(X_test)}")

    for model_name, model in models.items():
        print(f"🤖 Training {model_name} on {feat.upper()}...")

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        conf_matrix = confusion_matrix(y_test, y_pred)

        # Save confusion matrix CSV
        conf_df = pd.DataFrame(conf_matrix)
        conf_filename = f"confusion_{feat}_{model_name.replace(' ', '_').replace('(', '').replace(')', '')}.csv"
        conf_df.to_csv(os.path.join(results_dir, conf_filename), index=False)

        # Collect class-level metrics
        for label, metrics in report.items():
            if label not in ["accuracy", "macro avg", "weighted avg"]:
                all_results.append({
                    "Feature": feat.upper(),
                    "Model": model_name,
                    "Class": label,
                    "Precision": round(metrics["precision"], 4),
                    "Recall": round(metrics["recall"], 4),
                    "F1 Score": round(metrics["f1-score"], 4),
                    "Support": int(metrics["support"]),
                    "Accuracy": round(acc, 4)
                })

print("💾 Saving benchmark results...")
df_results = pd.DataFrame(all_results)
df_results.to_csv(summary_file, index=False)
print(f"✅ Results saved to {summary_file}")