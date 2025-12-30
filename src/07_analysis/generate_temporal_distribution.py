#!/usr/bin/env python3
"""
Generate temporal distribution CSV showing evolution of Peirce's diagrammatic practice.
Aggregates CLIP+Logistic Regression results by time period and category.
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path


def parse_year_range(start_year, end_year):
    """Parse start and end years, handling empty strings and creating ranges."""
    try:
        start = int(start_year) if start_year and str(start_year).strip() else None
        end = int(end_year) if end_year and str(end_year).strip() else None
        return start, end
    except (ValueError, TypeError):
        return None, None


def assign_period(start_year, end_year, bin_size=5):
    """
    Assign a time period to a manuscript based on its date range.
    Uses 5-year bins by default.
    """
    start, end = parse_year_range(start_year, end_year)

    if start is None and end is None:
        return "Undated"

    # Use the midpoint for range dating
    if start and end:
        midpoint = (start + end) // 2
    elif start:
        midpoint = start
    else:
        midpoint = end

    # Create period bins
    period_start = (midpoint // bin_size) * bin_size
    period_end = period_start + bin_size - 1

    return f"{period_start}-{period_end}"


def clean_category(category):
    """Remove letter prefix from category names."""
    if pd.isna(category):
        return category
    # Remove prefix like "A. ", "B. ", etc.
    import re
    cleaned = re.sub(r'^[A-Z]\.\s+', '', str(category))
    return cleaned


def main():
    # Load metadata
    print("Loading metadata...")
    with open('data/00_raw/metadata/collection_metadata.json', 'r') as f:
        metadata = json.load(f)

    metadata_df = pd.DataFrame(metadata)
    print(f"Loaded metadata for {len(metadata_df)} manuscripts")

    # Load classification results
    print("Loading classification results...")
    classified_df = pd.read_csv('data/02_results/classifications/classified_pages.csv')
    print(f"Loaded classifications for {len(classified_df)} pages")

    # Merge metadata with classifications
    print("Merging data...")
    merged_df = classified_df.merge(
        metadata_df[['ID', 'Start Year', 'End Year', 'Date']],
        on='ID',
        how='left'
    )

    # Assign time periods
    print("Assigning time periods...")
    merged_df['Period'] = merged_df.apply(
        lambda row: assign_period(row['Start Year'], row['End Year']),
        axis=1
    )

    # Clean category names
    merged_df['Category_Clean'] = merged_df['Category Level 2'].apply(clean_category)

    # Aggregate by period and category
    print("Aggregating data...")
    results = []

    for period in sorted(merged_df['Period'].unique(), key=lambda x: (x == "Undated", x)):
        for category in sorted(merged_df['Category_Clean'].unique()):
            if pd.isna(category):
                continue

            # Filter data for this period and category
            subset = merged_df[
                (merged_df['Period'] == period) &
                (merged_df['Category_Clean'] == category)
            ]

            if len(subset) == 0:
                continue

            total_pages = len(subset)
            pages_with_diagrams = len(subset[subset['Predicted_Label'] == 'diagram_mixed'])

            if total_pages > 0:
                percentage_diagrams = (pages_with_diagrams / total_pages) * 100
            else:
                percentage_diagrams = 0.0

            results.append({
                'year_range': period,
                'category': category,
                'total_pages': total_pages,
                'pages_with_diagrams': pages_with_diagrams,
                'percentage_diagrams': round(percentage_diagrams, 2)
            })

    # Create output DataFrame
    output_df = pd.DataFrame(results)

    # Sort by year range and category
    output_df = output_df.sort_values(['year_range', 'category']).reset_index(drop=True)

    # Save to CSV
    output_path = 'temporal_distribution_diagrams.csv'
    output_df.to_csv(output_path, index=False)

    print(f"\nTemporal distribution saved to: {output_path}")
    print(f"\nSummary statistics:")
    print(f"Total periods analyzed: {output_df['year_range'].nunique()}")
    print(f"Total categories: {output_df['category'].nunique()}")
    print(f"Total rows in output: {len(output_df)}")

    print(f"\nTime periods covered:")
    period_summary = output_df.groupby('year_range').agg({
        'total_pages': 'sum',
        'pages_with_diagrams': 'sum'
    }).reset_index()
    period_summary['percentage'] = (
        period_summary['pages_with_diagrams'] / period_summary['total_pages'] * 100
    ).round(2)
    print(period_summary.to_string(index=False))

    print(f"\nSample of temporal distribution (first 20 rows):")
    print(output_df.head(20).to_string(index=False))


if __name__ == '__main__':
    main()
