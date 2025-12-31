#!/usr/bin/env python3
"""
Calculate morphological evaluation metrics by comparing VLM predictions against ground truth.
"""

import json
from pathlib import Path
from collections import defaultdict
import pandas as pd


def load_ground_truth(filepath):
    """Load ground truth annotations from consolidated JSON."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Convert to dict keyed by diagram_id
    gt_dict = {}
    for diagram in data['diagrams']:
        gt_dict[diagram['diagram_id']] = {
            'cuts': diagram['cuts'],
            'lines': diagram['lines'],
            'spots': diagram['spots']
        }

    return gt_dict


def load_predictions(filepath):
    """Load VLM predictions from consolidated JSON."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    return data['evaluations']


def normalize_labels(labels):
    """Normalize labels to lowercase and strip whitespace for comparison."""
    if not labels:
        return set()
    return set(label.lower().strip() for label in labels)


def compare_prediction(prediction, ground_truth):
    """
    Compare a prediction against ground truth.

    Returns dict with boolean matches for each field.
    """
    if not prediction:
        return None

    results = {}

    # Cuts count
    results['cuts_count'] = (
        prediction.get('cuts', {}).get('count') == ground_truth['cuts']['count']
    )

    # Cuts nested
    results['cuts_nested'] = (
        prediction.get('cuts', {}).get('nested') == ground_truth['cuts']['nested']
    )

    # Lines count
    results['lines_count'] = (
        prediction.get('lines', {}).get('count') == ground_truth['lines']['count']
    )

    # Lines branching
    results['lines_branching'] = (
        prediction.get('lines', {}).get('branching') == ground_truth['lines']['branching']
    )

    # Spots count
    results['spots_count'] = (
        prediction.get('spots', {}).get('count') == ground_truth['spots']['count']
    )

    # Spots labels (set equality, order-independent, case-insensitive)
    pred_labels = normalize_labels(prediction.get('spots', {}).get('labels', []))
    gt_labels = normalize_labels(ground_truth['spots']['labels'])
    results['spots_labels'] = (pred_labels == gt_labels)

    # Calculate per-diagram accuracy
    correct = sum(results.values())
    total = len(results)
    results['accuracy'] = correct / total if total > 0 else 0

    return results


def calculate_metrics(ground_truth, predictions):
    """
    Calculate evaluation metrics for all predictions.

    Returns dict with per-model aggregated metrics.
    """
    model_results = defaultdict(lambda: defaultdict(list))
    detailed_results = []

    for eval_item in predictions:
        diagram_id = eval_item['diagram_id']
        model = eval_item['model']
        prediction = eval_item['prediction']

        # Skip if no ground truth for this diagram
        if diagram_id not in ground_truth:
            print(f"Warning: No ground truth for {diagram_id}")
            continue

        # Skip if prediction failed to parse
        if not prediction:
            print(f"Warning: Failed to parse prediction for {diagram_id} ({model})")
            continue

        # Compare prediction to ground truth
        comparison = compare_prediction(prediction, ground_truth[diagram_id])

        if comparison:
            # Store results for this model
            model_results[model]['cuts_count'].append(comparison['cuts_count'])
            model_results[model]['cuts_nested'].append(comparison['cuts_nested'])
            model_results[model]['lines_count'].append(comparison['lines_count'])
            model_results[model]['lines_branching'].append(comparison['lines_branching'])
            model_results[model]['spots_count'].append(comparison['spots_count'])
            model_results[model]['spots_labels'].append(comparison['spots_labels'])
            model_results[model]['accuracy'].append(comparison['accuracy'])

            # Store detailed results
            detailed_results.append({
                'diagram_id': diagram_id,
                'model': model,
                **comparison
            })

    # Calculate aggregated metrics per model
    aggregated = []
    for model, results in model_results.items():
        n = len(results['accuracy'])

        aggregated.append({
            'model': model,
            'num_evaluations': n,
            'avg_accuracy': round(100 * sum(results['accuracy']) / n, 2) if n > 0 else 0,
            'cuts_count_acc': round(100 * sum(results['cuts_count']) / n, 2) if n > 0 else 0,
            'cuts_nested_acc': round(100 * sum(results['cuts_nested']) / n, 2) if n > 0 else 0,
            'lines_count_acc': round(100 * sum(results['lines_count']) / n, 2) if n > 0 else 0,
            'lines_branching_acc': round(100 * sum(results['lines_branching']) / n, 2) if n > 0 else 0,
            'spots_count_acc': round(100 * sum(results['spots_count']) / n, 2) if n > 0 else 0,
            'spots_labels_acc': round(100 * sum(results['spots_labels']) / n, 2) if n > 0 else 0,
        })

    return aggregated, detailed_results


def main():
    # Paths
    gt_file = Path("data/03_ground_truth/ground_truth_morphological.json")
    pred_file = Path("data/03_ground_truth/morphological_predictions.json")
    output_file = Path("data/02_results/statistics/morphological_metrics.csv")
    detailed_file = Path("data/02_results/statistics/morphological_metrics_detailed.csv")

    print("Loading ground truth...")
    ground_truth = load_ground_truth(gt_file)
    print(f"  Loaded {len(ground_truth)} ground truth annotations")

    print("\nLoading predictions...")
    predictions = load_predictions(pred_file)
    print(f"  Loaded {len(predictions)} predictions")

    print("\nCalculating metrics...")
    aggregated, detailed = calculate_metrics(ground_truth, predictions)

    # Create DataFrames
    df_agg = pd.DataFrame(aggregated)
    df_detailed = pd.DataFrame(detailed)

    # Sort by avg_accuracy descending
    df_agg = df_agg.sort_values('avg_accuracy', ascending=False)

    # Save to CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_agg.to_csv(output_file, index=False)
    print(f"\nSaved aggregated metrics to {output_file}")

    df_detailed.to_csv(detailed_file, index=False)
    print(f"Saved detailed metrics to {detailed_file}")

    # Print summary
    print("\n" + "=" * 100)
    print("MORPHOLOGICAL EVALUATION METRICS")
    print("=" * 100)
    print(df_agg.to_string(index=False))
    print("=" * 100)

    # Print best model
    best = df_agg.iloc[0]
    print(f"\nBest performing model: {best['model']} ({best['avg_accuracy']}% average accuracy)")

    # Print per-feature best models
    print("\nBest per feature:")
    for col in ['cuts_count_acc', 'cuts_nested_acc', 'lines_count_acc',
                'lines_branching_acc', 'spots_count_acc', 'spots_labels_acc']:
        best_idx = df_agg[col].idxmax()
        best_model = df_agg.loc[best_idx, 'model']
        best_score = df_agg.loc[best_idx, col]
        feature_name = col.replace('_acc', '').replace('_', ' ').title()
        print(f"  {feature_name}: {best_model} ({best_score}%)")


if __name__ == "__main__":
    main()
