#!/usr/bin/env python3
"""
Evaluate VLM model results against manual ground truth annotations.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import pandas as pd


def extract_json_from_evaluation(evaluation_text):
    """Extract JSON from evaluation field which may contain markdown code blocks."""
    if not evaluation_text:
        return None

    # Remove markdown code blocks if present
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', evaluation_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = evaluation_text.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Text: {json_str[:200]}")
        return None


def load_ground_truth(gt_dir):
    """Load ground truth annotations."""
    gt_path = Path(gt_dir)
    ground_truth = {}

    for json_file in gt_path.glob("*.json"):
        diagram_id = json_file.stem
        with open(json_file, 'r') as f:
            gt_data = json.load(f)

        # Validate ground truth is complete
        if gt_data['cuts']['count'] is None:
            print(f"Warning: Ground truth incomplete for {diagram_id}")
            continue

        ground_truth[diagram_id] = gt_data

    return ground_truth


def load_model_evaluations(eval_dir):
    """Load model evaluation results."""
    eval_path = Path(eval_dir)
    evaluations = {}

    for json_file in eval_path.glob("*.json"):
        if json_file.name == "summary.json":
            continue

        diagram_id = json_file.stem
        with open(json_file, 'r') as f:
            data = json.load(f)

        eval_data = extract_json_from_evaluation(data.get('evaluation'))
        if eval_data:
            evaluations[diagram_id] = eval_data

    return evaluations


def evaluate_model(model_name, model_evals, ground_truth):
    """Evaluate a single model against ground truth."""
    results = {
        'model': model_name,
        'total_diagrams': len(ground_truth),
        'evaluated_diagrams': 0,
        'cuts_count_correct': 0,
        'cuts_nested_correct': 0,
        'lines_count_correct': 0,
        'lines_branching_correct': 0,
        'spots_count_correct': 0,
        'exact_match': 0,
        'missing_evaluations': [],
        'per_diagram': []
    }

    for diagram_id, gt in ground_truth.items():
        if diagram_id not in model_evals:
            results['missing_evaluations'].append(diagram_id)
            continue

        pred = model_evals[diagram_id]
        results['evaluated_diagrams'] += 1

        # Compare each field
        diagram_result = {
            'diagram_id': diagram_id,
            'cuts_count_match': False,
            'cuts_nested_match': False,
            'lines_count_match': False,
            'lines_branching_match': False,
            'spots_count_match': False,
        }

        # Cuts count
        if pred.get('cuts', {}).get('count') == gt['cuts']['count']:
            results['cuts_count_correct'] += 1
            diagram_result['cuts_count_match'] = True

        # Cuts nested
        if pred.get('cuts', {}).get('nested') == gt['cuts']['nested']:
            results['cuts_nested_correct'] += 1
            diagram_result['cuts_nested_match'] = True

        # Lines count
        if pred.get('lines', {}).get('count') == gt['lines']['count']:
            results['lines_count_correct'] += 1
            diagram_result['lines_count_match'] = True

        # Lines branching
        if pred.get('lines', {}).get('branching') == gt['lines']['branching']:
            results['lines_branching_correct'] += 1
            diagram_result['lines_branching_match'] = True

        # Spots count
        if pred.get('spots', {}).get('count') == gt['spots']['count']:
            results['spots_count_correct'] += 1
            diagram_result['spots_count_match'] = True

        # Exact match (all fields correct)
        if all([
            diagram_result['cuts_count_match'],
            diagram_result['cuts_nested_match'],
            diagram_result['lines_count_match'],
            diagram_result['lines_branching_match'],
            diagram_result['spots_count_match'],
        ]):
            results['exact_match'] += 1
            diagram_result['exact_match'] = True
        else:
            diagram_result['exact_match'] = False

        results['per_diagram'].append(diagram_result)

    return results


def calculate_metrics(results):
    """Calculate accuracy metrics as percentages."""
    n = results['evaluated_diagrams']
    if n == 0:
        return None

    return {
        'model': results['model'],
        'evaluated': f"{n}/{results['total_diagrams']}",
        'coverage': round(100 * n / results['total_diagrams'], 2),
        'exact_match': round(100 * results['exact_match'] / n, 2),
        'cuts_count_acc': round(100 * results['cuts_count_correct'] / n, 2),
        'cuts_nested_acc': round(100 * results['cuts_nested_correct'] / n, 2),
        'lines_count_acc': round(100 * results['lines_count_correct'] / n, 2),
        'lines_branching_acc': round(100 * results['lines_branching_correct'] / n, 2),
        'spots_count_acc': round(100 * results['spots_count_correct'] / n, 2),
    }


def main():
    # Paths
    gt_dir = Path("data/03_ground_truth/morphological")
    eval_base = Path("data/02_results/diagram_evaluations")

    # Model evaluation directories (use latest for each)
    models = {
        "Claude Sonnet 4.5": "claude_sonnet_4_5_20250929/eval_20251231_155722",
        "Gemini 3 Pro": "google/gemini_3_pro_preview/eval_20251231_155724",
        "Gemini 3 Flash": "google/gemini_3_flash_preview/eval_20251231_162141",
        "Gemma 3 27B": "gemma_3_27b_it/eval_20251231_155725",
        "Qwen 2.5 VL 72B": "qwen2_5_vl_72b_instruct/eval_20251231_155726",
    }

    # Load ground truth
    print("Loading ground truth annotations...")
    ground_truth = load_ground_truth(gt_dir)
    print(f"Loaded {len(ground_truth)} ground truth annotations")
    print()

    # Evaluate each model
    all_results = []
    detailed_results = []

    for model_name, eval_path in models.items():
        print(f"Evaluating {model_name}...")
        eval_dir = eval_base / eval_path

        if not eval_dir.exists():
            print(f"  Warning: Evaluation directory not found")
            continue

        # Load model evaluations
        model_evals = load_model_evaluations(eval_dir)
        print(f"  Loaded {len(model_evals)} evaluations")

        # Evaluate
        results = evaluate_model(model_name, model_evals, ground_truth)

        # Calculate metrics
        metrics = calculate_metrics(results)
        if metrics:
            all_results.append(metrics)

        # Add detailed results
        for diagram_result in results['per_diagram']:
            detailed_results.append({
                'model': model_name,
                **diagram_result
            })

        # Print summary
        if results['missing_evaluations']:
            print(f"  Missing {len(results['missing_evaluations'])} evaluations")

        print(f"  Exact match: {results['exact_match']}/{results['evaluated_diagrams']} ({metrics['exact_match']}%)")
        print()

    # Create comparison DataFrame
    df = pd.DataFrame(all_results)

    # Reorder columns for better readability
    column_order = [
        'model', 'evaluated', 'coverage', 'exact_match',
        'cuts_count_acc', 'cuts_nested_acc',
        'lines_count_acc', 'lines_branching_acc',
        'spots_count_acc'
    ]
    df = df[column_order]

    # Save results
    output_dir = Path("data/02_results/statistics")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_file = output_dir / "ground_truth_evaluation_summary.csv"
    df.to_csv(summary_file, index=False)
    print(f"Saved summary to {summary_file}")

    # Save detailed per-diagram results
    detailed_df = pd.DataFrame(detailed_results)
    detailed_file = output_dir / "ground_truth_evaluation_detailed.csv"
    detailed_df.to_csv(detailed_file, index=False)
    print(f"Saved detailed results to {detailed_file}")

    # Print summary table
    print()
    print("=" * 100)
    print("GROUND TRUTH EVALUATION SUMMARY")
    print("=" * 100)
    print(df.to_string(index=False))
    print("=" * 100)

    # Print best performing model
    print()
    best_model = df.loc[df['exact_match'].idxmax()]
    print(f"Best performing model (exact match): {best_model['model']} ({best_model['exact_match']}%)")
    print()

    # Print per-feature best models
    print("Best per feature:")
    print(f"  Cuts count: {df.loc[df['cuts_count_acc'].idxmax(), 'model']} ({df['cuts_count_acc'].max()}%)")
    print(f"  Cuts nested: {df.loc[df['cuts_nested_acc'].idxmax(), 'model']} ({df['cuts_nested_acc'].max()}%)")
    print(f"  Lines count: {df.loc[df['lines_count_acc'].idxmax(), 'model']} ({df['lines_count_acc'].max()}%)")
    print(f"  Lines branching: {df.loc[df['lines_branching_acc'].idxmax(), 'model']} ({df['lines_branching_acc'].max()}%)")
    print(f"  Spots count: {df.loc[df['spots_count_acc'].idxmax(), 'model']} ({df['spots_count_acc'].max()}%)")


if __name__ == "__main__":
    main()
