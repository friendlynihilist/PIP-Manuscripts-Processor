#!/usr/bin/env python3
"""
Consolidate all VLM predictions into a single JSON file for analysis.
"""

import json
import re
from pathlib import Path


def extract_json_from_evaluation(evaluation_text):
    """Extract JSON from evaluation field which may contain markdown code blocks."""
    if not evaluation_text:
        return None

    # Remove markdown code blocks if present
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', evaluation_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find JSON in the text
        json_match = re.search(r'\{[^{}]*"cuts"[^{}]*"lines"[^{}]*"spots"[^{}]*\}', evaluation_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = evaluation_text.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def consolidate_predictions():
    """Consolidate all VLM predictions into a single file."""
    base_dir = Path("data/02_results/diagram_evaluations")

    models = {
        "Claude Sonnet 4.5": ("claude_sonnet_4_5_20250929/eval_20251231_155722", "claude-sonnet-4-5-20250929"),
        "Gemini 3 Pro": ("google/gemini_3_pro_preview/eval_20251231_155724", "google/gemini-3-pro-preview"),
        "Gemini 3 Flash": ("google/gemini_3_flash_preview/eval_20251231_162141", "google/gemini-3-flash-preview"),
        "Gemma 3 27B": ("gemma_3_27b_it/eval_20251231_155725", "gemma-3-27b-it"),
        "Qwen 2.5 VL 72B": ("qwen2_5_vl_72b_instruct/eval_20251231_155726", "qwen2.5-vl-72b-instruct"),
    }

    evaluations = []

    for model_name, (eval_path, model_id) in models.items():
        eval_dir = base_dir / eval_path

        if not eval_dir.exists():
            print(f"Warning: {eval_dir} not found")
            continue

        print(f"Loading {model_name}...")

        for json_file in sorted(eval_dir.glob("*.json")):
            if json_file.name == "summary.json":
                continue

            with open(json_file, 'r') as f:
                data = json.load(f)

            diagram_id = json_file.stem
            raw_response = data.get('evaluation', '')

            # Parse prediction
            prediction = extract_json_from_evaluation(raw_response)

            evaluation = {
                "diagram_id": diagram_id,
                "model": model_name,
                "model_id": model_id,
                "prediction": prediction,
                "raw_response": raw_response,
                "timestamp": data.get('timestamp', '')
            }

            evaluations.append(evaluation)

    # Create output structure
    output = {
        "evaluations": evaluations,
        "metadata": {
            "total_evaluations": len(evaluations),
            "models": list(models.keys()),
            "source": "Automated consolidation from data/02_results/diagram_evaluations/",
            "format_version": "1.0"
        }
    }

    # Save to file
    output_file = Path("data/03_ground_truth/morphological_predictions.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print(f"Created {output_file}")
    print(f"Total evaluations: {len(evaluations)}")

    # Print breakdown by model
    model_counts = {}
    for eval in evaluations:
        model_counts[eval['model']] = model_counts.get(eval['model'], 0) + 1

    print("\nEvaluations per model:")
    for model, count in sorted(model_counts.items()):
        print(f"  {model}: {count}")


if __name__ == "__main__":
    consolidate_predictions()
