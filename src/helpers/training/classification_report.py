import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix
import pandas as pd

# === CONFIGURATION ===
models_info = [
    {
        "name": "HOG + SVM RBF Tuned",
        "model_path": "models/svm_rbf_tuned_hog.pkl",
        "X_test_path": "preprocessed_data_hog/X_test.npy",
        "y_test_path": "preprocessed_data_hog/y_test.npy",
        "label_encoder_path": "preprocessed_data_hog/label_encoder.pkl"
    },
    {
        "name": "CLIP + Linear SVM",
        "model_path": "models/linear_svm_clip.pkl",
        "X_test_path": "preprocessed_data_clip/X_clip_test.npy",
        "y_test_path": "preprocessed_data_clip/y_clip_test.npy",
        "label_encoder_path": "preprocessed_data_clip/label_encoder.pkl"
    }
]

# === EXECUTION ===
all_results = []

for info in models_info:
    print(f"🔍 Evaluating {info['name']}...")
    
    # Load model and data
    with open(info["model_path"], "rb") as f:
        model = joblib.load(f)
    X_test = np.load(info["X_test_path"])
    y_test = np.load(info["y_test_path"])
    
    # Load label encoder
    with open(info["label_encoder_path"], "rb") as f:
        label_encoder = joblib.load(f)
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Metrics
    report = classification_report(y_test, y_pred, output_dict=True, target_names=label_encoder.classes_)
    conf_matrix = confusion_matrix(y_test, y_pred)

    # Save precision, recall, f1 for each class
    for label in label_encoder.classes_:
        all_results.append({
            "Model": info["name"],
            "Class": label,
            "Precision": report[label]["precision"],
            "Recall": report[label]["recall"],
            "F1-Score": report[label]["f1-score"],
            "Support": report[label]["support"]
        })
    
    # Save confusion matrix separately if needed
    conf_df = pd.DataFrame(conf_matrix, 
                           index=label_encoder.classes_, 
                           columns=label_encoder.classes_)
    conf_df.to_csv(f"confusion_matrix_{info['name'].replace(' ', '_').replace('+', '').lower()}.csv")
    print(f"✅ Confusion matrix saved for {info['name']}")

# --- Save all class reports ---
df_results = pd.DataFrame(all_results)
df_results.to_csv("detailed_classification_report.csv", index=False)
print("✅ Detailed classification report saved: detailed_classification_report.csv")