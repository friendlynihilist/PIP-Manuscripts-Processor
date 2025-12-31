#!/usr/bin/env python3
"""
Compare VLM model evaluations on morphological diagram analysis.
Analyzes JSON outputs from Claude, Gemini, Gemma, and Qwen evaluations.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import pandas as pd


def extract_json_from_evaluation(evaluation_text):
    """Extract JSON from evaluation field which may contain markdown code blocks."""
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


def load_evaluations(base_dir):
    """Load all evaluation JSON files from the results directory."""
    base_path = Path(base_dir)
    evaluations = defaultdict(list)

    models = {
        'claude_sonnet_4_5_20250929': 'Claude Sonnet 4.5',
        'google/gemini_3_pro_preview': 'Gemini 3 Pro',
        'gemma_3_27b_it': 'Gemma 3 27B',
        'qwen2_5_vl_72b_instruct': 'Qwen 2.5 VL 72B'
    }

    for model_dir, model_name in models.items():
        model_path = base_path / model_dir
        if not model_path.exists():
            print(f"Warning: {model_path} not found")
            continue

        # Find the most recent evaluation directory
        eval_dirs = sorted([d for d in model_path.iterdir() if d.is_dir() and d.name.startswith('eval_')])
        if not eval_dirs:
            print(f"Warning: No evaluation directories found in {model_path}")
            continue

        latest_eval = eval_dirs[-1]
        print(f"Loading {model_name} from {latest_eval.name}")

        for json_file in latest_eval.glob('*.json'):
            # Skip summary files
            if json_file.name == 'summary.json':
                continue

            with open(json_file, 'r') as f:
                data = json.load(f)

            # Create unique identifier for this diagram
            diagram_id = f"{data['page_filename']}_{data['segment_index']}"

            # Parse the evaluation JSON
            eval_data = extract_json_from_evaluation(data['evaluation'])

            if eval_data:
                evaluations[diagram_id].append({
                    'model': model_name,
                    'manuscript_id': data['manuscript_id'],
                    'page_filename': data['page_filename'],
                    'segment_index': data['segment_index'],
                    'cuts_count': eval_data.get('cuts', {}).get('count', None),
                    'cuts_nested': eval_data.get('cuts', {}).get('nested', None),
                    'lines_count': eval_data.get('lines', {}).get('count', None),
                    'lines_branching': eval_data.get('lines', {}).get('branching', None),
                    'spots_count': eval_data.get('spots', {}).get('count', None),
                    'spots_labels': eval_data.get('spots', {}).get('labels', []),
                    'timestamp': data['timestamp']
                })

    return evaluations


def compare_evaluations(evaluations):
    """Compare evaluations across models for each diagram."""
    comparison_rows = []

    for diagram_id, evals in sorted(evaluations.items()):
        if len(evals) < 2:
            continue  # Skip if we don't have multiple models

        # Get base info from first evaluation
        base = evals[0]

        # Check agreement on counts
        cuts_counts = [e['cuts_count'] for e in evals if e['cuts_count'] is not None]
        lines_counts = [e['lines_count'] for e in evals if e['lines_count'] is not None]
        spots_counts = [e['spots_count'] for e in evals if e['spots_count'] is not None]

        cuts_agreement = len(set(cuts_counts)) == 1 if cuts_counts else False
        lines_agreement = len(set(lines_counts)) == 1 if lines_counts else False
        spots_agreement = len(set(spots_counts)) == 1 if spots_counts else False

        comparison_rows.append({
            'diagram_id': diagram_id,
            'page': base['page_filename'],
            'segment': base['segment_index'],
            'num_models': len(evals),
            'cuts_agreement': cuts_agreement,
            'cuts_values': ', '.join(f"{e['model']}: {e['cuts_count']}" for e in evals if e['cuts_count'] is not None),
            'lines_agreement': lines_agreement,
            'lines_values': ', '.join(f"{e['model']}: {e['lines_count']}" for e in evals if e['lines_count'] is not None),
            'spots_agreement': spots_agreement,
            'spots_values': ', '.join(f"{e['model']}: {e['spots_count']}" for e in evals if e['spots_count'] is not None),
        })

    return pd.DataFrame(comparison_rows)


def create_detailed_comparison(evaluations):
    """Create detailed per-diagram comparison table."""
    rows = []

    for diagram_id, evals in sorted(evaluations.items()):
        for eval_data in evals:
            rows.append({
                'diagram_id': diagram_id,
                'page': eval_data['page_filename'],
                'segment': eval_data['segment_index'],
                'model': eval_data['model'],
                'cuts_count': eval_data['cuts_count'],
                'cuts_nested': eval_data['cuts_nested'],
                'lines_count': eval_data['lines_count'],
                'lines_branching': eval_data['lines_branching'],
                'spots_count': eval_data['spots_count'],
                'spots_labels': '|'.join(eval_data['spots_labels']) if eval_data['spots_labels'] else '',
            })

    return pd.DataFrame(rows)


def calculate_summary_stats(evaluations):
    """Calculate summary statistics across all evaluations."""
    stats = defaultdict(lambda: defaultdict(int))

    for diagram_id, evals in evaluations.items():
        if len(evals) < 2:
            continue

        # Count agreements
        cuts_counts = [e['cuts_count'] for e in evals if e['cuts_count'] is not None]
        lines_counts = [e['lines_count'] for e in evals if e['lines_count'] is not None]
        spots_counts = [e['spots_count'] for e in evals if e['spots_count'] is not None]

        stats['total']['diagrams'] += 1

        if len(set(cuts_counts)) == 1:
            stats['agreement']['cuts'] += 1
        if len(set(lines_counts)) == 1:
            stats['agreement']['lines'] += 1
        if len(set(spots_counts)) == 1:
            stats['agreement']['spots'] += 1

    summary_rows = []
    total = stats['total']['diagrams']

    summary_rows.append({
        'metric': 'Total diagrams compared',
        'value': total,
        'percentage': 100.0
    })
    summary_rows.append({
        'metric': 'Cuts count agreement',
        'value': stats['agreement']['cuts'],
        'percentage': round(100 * stats['agreement']['cuts'] / total, 2) if total > 0 else 0
    })
    summary_rows.append({
        'metric': 'Lines count agreement',
        'value': stats['agreement']['lines'],
        'percentage': round(100 * stats['agreement']['lines'] / total, 2) if total > 0 else 0
    })
    summary_rows.append({
        'metric': 'Spots count agreement',
        'value': stats['agreement']['spots'],
        'percentage': round(100 * stats['agreement']['spots'] / total, 2) if total > 0 else 0
    })

    return pd.DataFrame(summary_rows)


def main():
    base_dir = Path('data/02_results/diagram_evaluations')
    output_dir = Path('data/02_results/statistics')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading evaluations...")
    evaluations = load_evaluations(base_dir)

    print(f"\nFound evaluations for {len(evaluations)} diagrams")

    # Create comparison dataframe
    print("\nGenerating comparison analysis...")
    comparison_df = compare_evaluations(evaluations)
    comparison_output = output_dir / 'vlm_evaluation_comparison.csv'
    comparison_df.to_csv(comparison_output, index=False)
    print(f"Saved comparison to {comparison_output}")

    # Create detailed results table
    print("\nGenerating detailed results...")
    detailed_df = create_detailed_comparison(evaluations)
    detailed_output = output_dir / 'vlm_evaluation_detailed.csv'
    detailed_df.to_csv(detailed_output, index=False)
    print(f"Saved detailed results to {detailed_output}")

    # Calculate summary statistics
    print("\nCalculating summary statistics...")
    summary_df = calculate_summary_stats(evaluations)
    summary_output = output_dir / 'vlm_evaluation_summary.csv'
    summary_df.to_csv(summary_output, index=False)
    print(f"Saved summary statistics to {summary_output}")

    # Print summary to console
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print(summary_df.to_string(index=False))

    print("\n" + "="*60)
    print("AGREEMENT ANALYSIS")
    print("="*60)
    print(f"Total diagrams with multiple model evaluations: {len(comparison_df)}")
    print(f"Cuts count perfect agreement: {comparison_df['cuts_agreement'].sum()} ({100*comparison_df['cuts_agreement'].mean():.1f}%)")
    print(f"Lines count perfect agreement: {comparison_df['lines_agreement'].sum()} ({100*comparison_df['lines_agreement'].mean():.1f}%)")
    print(f"Spots count perfect agreement: {comparison_df['spots_agreement'].sum()} ({100*comparison_df['spots_agreement'].mean():.1f}%)")

    # Show disagreements
    print("\n" + "="*60)
    print("DISAGREEMENTS")
    print("="*60)

    disagreements = comparison_df[
        ~comparison_df['cuts_agreement'] |
        ~comparison_df['lines_agreement'] |
        ~comparison_df['spots_agreement']
    ]

    if len(disagreements) > 0:
        print(f"\nFound {len(disagreements)} diagrams with disagreements:\n")
        for _, row in disagreements.iterrows():
            print(f"\n{row['diagram_id']}:")
            if not row['cuts_agreement']:
                print(f"  Cuts: {row['cuts_values']}")
            if not row['lines_agreement']:
                print(f"  Lines: {row['lines_values']}")
            if not row['spots_agreement']:
                print(f"  Spots: {row['spots_values']}")
    else:
        print("\nNo disagreements found - all models agree perfectly!")


if __name__ == '__main__':
    main()
