#!/usr/bin/env python3
"""
Generate corpus distribution CSV by Peirce's manuscript categories.
Aggregates CLIP+Logistic Regression classification results.
"""

import pandas as pd
from pathlib import Path


def main():
    # Read the full corpus classification results
    classified_df = pd.read_csv('data/02_results/classifications/classified_pages.csv')

    # Group by category
    results = []

    for category in sorted(classified_df['Category Level 2'].unique()):
        if pd.isna(category):
            continue

        # Filter pages for this category
        category_pages = classified_df[classified_df['Category Level 2'] == category]

        # Total pages in this category
        total_pages = len(category_pages)

        # Count pages with diagrams (Predicted_Label == 'diagram_mixed')
        # diagram_mixed = pages that contain diagrams (possibly with text too)
        pages_with_diagrams = category_pages[
            category_pages['Predicted_Label'] == 'diagram_mixed'
        ]
        num_pages_with_diagrams = len(pages_with_diagrams)

        # Calculate percentage
        if total_pages > 0:
            percentage_diagrams = (num_pages_with_diagrams / total_pages) * 100
        else:
            percentage_diagrams = 0.0

        results.append({
            'category': category,
            'total_pages': total_pages,
            'pages_with_diagrams': num_pages_with_diagrams,
            'percentage_diagrams': round(percentage_diagrams, 2)
        })

    # Create output DataFrame
    output_df = pd.DataFrame(results)

    # Save to CSV
    output_path = 'corpus_distribution_by_category.csv'
    output_df.to_csv(output_path, index=False)

    print(f"Corpus distribution saved to: {output_path}")
    print(f"\nSummary:")
    print(output_df.to_string(index=False))
    print(f"\nTotal categories: {len(output_df)}")
    print(f"Total pages in corpus: {len(classified_df)}")

    # Show prediction label distribution
    print(f"\nPrediction label distribution:")
    print(classified_df['Predicted_Label'].value_counts())


if __name__ == '__main__':
    main()
