#!/usr/bin/env python3
"""
Generate distribution CSV for manually annotated pages used in page-level classification.
Shows the training data distribution for CLIP + Logistic Regression classifier.
"""

import numpy as np
import pickle
import pandas as pd


def main():
    # Load training and test labels
    y_train = np.load('data/01_intermediate/embeddings/y_train.npy')
    y_test = np.load('data/01_intermediate/embeddings/y_test.npy')

    # Load label encoder
    with open('data/01_intermediate/embeddings/label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)

    # Combine train and test for total annotated distribution
    y_all = np.concatenate([y_train, y_test])

    print("=== Annotated Dataset Summary ===")
    print(f"Training samples: {len(y_train)}")
    print(f"Test samples: {len(y_test)}")
    print(f"Total annotated: {len(y_all)}")
    print(f"Classes: {label_encoder.classes_}")

    # Create distribution for all annotated data
    results_all = []
    total_all = len(y_all)

    for class_idx, class_name in enumerate(label_encoder.classes_):
        count = np.sum(y_all == class_idx)
        percentage = (count / total_all) * 100

        # Capitalize first letter for better display
        display_name = class_name.replace('_', ' ').title()

        results_all.append({
            'class': display_name,
            'count': int(count),
            'percentage': round(percentage, 2)
        })

    # Create output DataFrame
    output_df = pd.DataFrame(results_all)

    # Save to CSV
    output_path = 'page_classification_training_distribution.csv'
    output_df.to_csv(output_path, index=False)

    print(f"\nDistribution saved to: {output_path}")
    print(f"\n=== Full Annotated Dataset Distribution ===")
    print(output_df.to_string(index=False))

    # Also print training-only distribution for reference
    print(f"\n=== Training Set Only Distribution ===")
    for class_idx, class_name in enumerate(label_encoder.classes_):
        train_count = np.sum(y_train == class_idx)
        train_pct = (train_count / len(y_train)) * 100
        display_name = class_name.replace('_', ' ').title()
        print(f"{display_name}: {train_count} ({train_pct:.2f}%)")

    print(f"\n=== Test Set Distribution ===")
    for class_idx, class_name in enumerate(label_encoder.classes_):
        test_count = np.sum(y_test == class_idx)
        test_pct = (test_count / len(y_test)) * 100
        display_name = class_name.replace('_', ' ').title()
        print(f"{display_name}: {test_count} ({test_pct:.2f}%)")


if __name__ == '__main__':
    main()
