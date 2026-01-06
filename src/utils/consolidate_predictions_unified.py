#!/usr/bin/env python3
"""
Unified script to consolidate VLM predictions for different evaluation types.
Supports: morphological, indexical, symbolic
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================================
# CONFIGURATION
# ============================================================================

EVALUATION_TYPES = {
    "morphological": {
        "output_file": "data/03_ground_truth/morphological_predictions.json",
        "parse_json": True,
        "prompt_filter": None,
        "description": "Morphological analysis (cuts, lines, spots)"
    },
    "indexical": {
        "output_file": "data/03_ground_truth/indexical_predictions.json",
        "parse_json": False,
        "prompt_filter": None,
        "description": "Indexical/spatial relationships"
    },
    "symbolic": {
        "output_file": "data/03_ground_truth/symbolic_predictions.json",
        "parse_json": False,
        "prompt_filter": "EXISTENTIAL GRAPH INTERPRETATION",
        "description": "Symbolic/logical interpretation"
    }
}

# Model configurations
MODELS = {
    "Claude Sonnet 4.5": "claude_sonnet_4_5_20250929",
    "Gemini 3 Pro": "google/gemini_3_pro_preview",
    "Gemini 3 Flash": "google/gemini_3_flash_preview",
    "Gemma 3 27B": "gemma_3_27b_it",
    "Qwen 2.5 VL 72B": "qwen2_5_vl_72b_instruct",
}

BASE_DIR = Path("data/02_results/diagram_evaluations")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_json_from_evaluation(evaluation_text: str) -> Optional[Dict]:
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


def consolidate_predictions(eval_type: str, date_filter: Optional[str] = None,
                           specific_eval_dirs: Optional[Dict[str, str]] = None) -> None:
    """
    Consolidate all VLM predictions for a specific evaluation type.

    Args:
        eval_type: Type of evaluation (morphological, indexical, symbolic)
        date_filter: Optional date filter for eval directories (e.g., "20260101")
        specific_eval_dirs: Optional dict mapping model names to specific eval directories
    """
    if eval_type not in EVALUATION_TYPES:
        raise ValueError(f"Invalid evaluation type: {eval_type}. Must be one of {list(EVALUATION_TYPES.keys())}")

    config = EVALUATION_TYPES[eval_type]
    print(f"Consolidating {eval_type} predictions...")
    print(f"Description: {config['description']}\n")

    evaluations = []

    for model_name, model_path in MODELS.items():
        model_dir = BASE_DIR / model_path

        if not model_dir.exists():
            print(f"Warning: {model_dir} not found")
            continue

        print(f"Loading {model_name}...")

        # Determine which evaluation directories to use
        if specific_eval_dirs and model_name in specific_eval_dirs:
            # Use specific directory if provided
            eval_dirs = [BASE_DIR / specific_eval_dirs[model_name]]
        elif date_filter:
            # Find all evaluation directories matching the date filter
            eval_dirs = sorted(model_dir.glob(f"eval_{date_filter}_*"))
        else:
            # Use all evaluation directories
            eval_dirs = sorted(model_dir.glob("eval_*"))

        if not eval_dirs:
            print(f"  Warning: No evaluation directories found for {model_name}")
            continue

        # Process all JSON files from all evaluation directories
        diagram_ids_seen = set()

        for eval_dir in eval_dirs:
            for json_file in eval_dir.glob("hou02614c00458*.json"):
                # Skip summary files
                if json_file.name == "summary.json":
                    continue

                # Extract diagram_id from filename
                diagram_id = json_file.stem

                # Skip if we've already processed this diagram for this model
                if diagram_id in diagram_ids_seen:
                    continue

                # Read the evaluation data
                with open(json_file, 'r') as f:
                    data = json.load(f)

                # Apply prompt filter if specified
                if config['prompt_filter']:
                    prompt = data.get('prompt', '')
                    if not prompt.startswith(config['prompt_filter']):
                        continue

                diagram_ids_seen.add(diagram_id)

                # Extract the prediction
                raw_response = data.get('evaluation', '')

                if config['parse_json']:
                    # For morphological: parse JSON structure
                    prediction = extract_json_from_evaluation(raw_response)
                else:
                    # For indexical/symbolic: store raw text
                    prediction = raw_response

                evaluation = {
                    "diagram_id": diagram_id,
                    "model": model_name,
                    "model_id": data.get('model', ''),
                    "prediction": prediction,
                    "timestamp": data.get('timestamp', '')
                }

                # Include raw_response for morphological evaluations
                if config['parse_json']:
                    evaluation["raw_response"] = raw_response

                evaluations.append(evaluation)

        print(f"  Loaded {len(diagram_ids_seen)} diagrams")

    # Create output structure
    output = {
        "evaluations": evaluations,
        "metadata": {
            "total_evaluations": len(evaluations),
            "models": list(MODELS.keys()),
            "evaluation_type": eval_type,
            "source": "Automated consolidation from data/02_results/diagram_evaluations/",
            "format_version": "1.0"
        }
    }

    # Save to file
    output_file = Path(config['output_file'])
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print(f"✓ Created {output_file}")
    print(f"  Total evaluations: {len(evaluations)}")
    print(f"  Evaluation type: {eval_type}")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Consolidate VLM predictions for different evaluation types"
    )
    parser.add_argument(
        "eval_type",
        choices=list(EVALUATION_TYPES.keys()),
        help="Type of evaluation to consolidate"
    )
    parser.add_argument(
        "--date",
        help="Filter evaluation directories by date (e.g., 20260101)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Consolidate all evaluation types"
    )

    args = parser.parse_args()

    if args.all:
        # Process all evaluation types
        for eval_type in EVALUATION_TYPES.keys():
            consolidate_predictions(eval_type, date_filter=args.date)
            print()
    else:
        # Process single evaluation type
        consolidate_predictions(args.eval_type, date_filter=args.date)


if __name__ == "__main__":
    main()
