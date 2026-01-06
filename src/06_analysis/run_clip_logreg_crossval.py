#!/usr/bin/env python3
"""
Run 10-fold cross-validation on CLIP + Logistic Regression classifier.
Generates per-fold metrics for analysis.
"""

import numpy as np
import pandas as pd
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import precision_recall_fscore_support, accuracy_score


def main():
    print("Loading training data...")

    # Load training data
    X_train = np.load('data/01_intermediate/embeddings/X_train_clip.npy')
    y_train = np.load('data/01_intermediate/embeddings/y_train.npy')

    # Load label encoder
    with open('data/01_intermediate/embeddings/label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)

    print(f"Training samples: {len(X_train)}")
    print(f"Classes: {label_encoder.classes_}")

    # Initialize classifier (same parameters as in the original training)
    clf = LogisticRegression(
        penalty='l2',
        solver='lbfgs',
        max_iter=1000,
        C=1.0,
        random_state=42
    )

    # 10-fold cross-validation
    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

    print("\nRunning 10-fold cross-validation...")

    fold_results = []

    for fold_idx, (train_idx, val_idx) in enumerate(cv.split(X_train, y_train), 1):
        X_fold_train, X_fold_val = X_train[train_idx], X_train[val_idx]
        y_fold_train, y_fold_val = y_train[train_idx], y_train[val_idx]

        # Train model on this fold
        clf.fit(X_fold_train, y_fold_train)

        # Predict on validation set
        y_pred = clf.predict(X_fold_val)

        # Calculate metrics (macro-averaged)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_fold_val, y_pred, average='macro', zero_division=0
        )
        accuracy = accuracy_score(y_fold_val, y_pred)

        fold_results.append({
            'fold': fold_idx,
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'accuracy': round(accuracy, 4)
        })

        print(f"Fold {fold_idx:2d}: Accuracy={accuracy:.4f}, "
              f"Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")

    # Create DataFrame
    results_df = pd.DataFrame(fold_results)

    # Save to CSV
    output_path = 'clip_logreg_crossval_folds.csv'
    results_df.to_csv(output_path, index=False)

    print(f"\n✅ Results saved to: {output_path}")

    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Accuracy:  mean={results_df['accuracy'].mean():.4f}, "
          f"std={results_df['accuracy'].std():.4f}")
    print(f"Precision: mean={results_df['precision'].mean():.4f}, "
          f"std={results_df['precision'].std():.4f}")
    print(f"Recall:    mean={results_df['recall'].mean():.4f}, "
          f"std={results_df['recall'].std():.4f}")
    print(f"F1 Score:  mean={results_df['f1_score'].mean():.4f}, "
          f"std={results_df['f1_score'].std():.4f}")

    print("\n=== Full Results ===")
    print(results_df.to_string(index=False))


if __name__ == '__main__':
    main()
