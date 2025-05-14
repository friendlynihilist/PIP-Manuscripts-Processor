import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# === Load CLIP features and labels ===
X_train = np.load("preprocessed_data/X_train_clip.npy")
X_test = np.load("preprocessed_data/X_test_clip.npy")
y_train = np.load("preprocessed_data/y_train.npy")
y_test = np.load("preprocessed_data/y_test.npy")

# === Define pipeline: scaler + logistic regression ===
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("logreg", LogisticRegression(max_iter=1000))
])

# === Define hyperparameter grid ===
param_grid = {
    "logreg__C": [0.01, 0.1, 1, 10, 100],
    "logreg__penalty": ["l2"],
    "logreg__solver": ["lbfgs", "liblinear"]
}

# === Grid search with 5-fold CV ===
grid = GridSearchCV(pipeline, param_grid, cv=5, scoring="f1_macro", n_jobs=-1, verbose=1)
grid.fit(X_train, y_train)

# === Save the best model ===
joblib.dump(grid.best_estimator_, "best_logreg_clip_model.pkl")

# === Evaluate on test set ===
y_pred = grid.predict(X_test)
print("\nBest parameters:", grid.best_params_)
print("\nClassification report on test set:")
print(classification_report(y_test, y_pred))
print("\nConfusion matrix:")
print(confusion_matrix(y_test, y_pred))