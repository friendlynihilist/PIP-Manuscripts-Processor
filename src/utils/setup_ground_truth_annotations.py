#!/usr/bin/env python3
"""
Setup ground truth annotation structure.
Creates folders for morphological, indexical, and symbolic annotations
with diagram images and JSON templates.
"""

import json
import shutil
from pathlib import Path


def create_morphological_template():
    """Create the morphological evaluation template."""
    return {
        "cuts": {
            "count": None,
            "nested": None
        },
        "lines": {
            "count": None,
            "branching": None
        },
        "spots": {
            "count": None,
            "labels": []
        }
    }


def create_indexical_template():
    """Create the indexical evaluation template (placeholder)."""
    return {
        "note": "Indexical level annotation template - to be defined"
    }


def create_symbolic_template():
    """Create the symbolic evaluation template (placeholder)."""
    return {
        "note": "Symbolic level annotation template - to be defined"
    }


def setup_ground_truth(evaluation_dir, output_base):
    """
    Setup ground truth annotation structure from evaluation results.

    Args:
        evaluation_dir: Path to evaluation directory with JSON files
        output_base: Base path for ground truth annotations
    """
    eval_path = Path(evaluation_dir)
    base_path = Path(output_base)

    # Create level directories
    levels = {
        'morphological': create_morphological_template,
        'indexical': create_indexical_template,
        'symbolic': create_symbolic_template
    }

    for level in levels:
        (base_path / level).mkdir(parents=True, exist_ok=True)

    # Process each evaluation JSON file
    json_files = sorted([f for f in eval_path.glob('*.json') if f.name != 'summary.json'])

    print(f"Setting up ground truth annotations for {len(json_files)} diagrams...")

    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)

        # Get diagram info
        crop_path = Path(data['crop_path'])
        base_name = crop_path.stem  # e.g., "D._Logic__hou02614c00458__seq15_cls0_0"

        # Create a cleaner name using the evaluation filename (without extension)
        clean_name = json_file.stem

        if not crop_path.exists():
            print(f"Warning: Image not found: {crop_path}")
            continue

        # Copy image and create JSON template for each level
        for level, template_func in levels.items():
            level_path = base_path / level

            # Copy image
            image_dest = level_path / f"{clean_name}.jpg"
            if not image_dest.exists():
                shutil.copy2(crop_path, image_dest)
                print(f"  Copied {clean_name}.jpg to {level}/")

            # Create JSON template
            json_dest = level_path / f"{clean_name}.json"
            if not json_dest.exists():
                template = template_func()
                with open(json_dest, 'w') as f:
                    json.dump(template, f, indent=2)
                print(f"  Created {clean_name}.json in {level}/")

    print(f"\nGround truth structure created successfully!")
    print(f"Location: {output_base}")
    print(f"\nLevels:")
    for level in levels:
        level_path = base_path / level
        num_images = len(list(level_path.glob('*.jpg')))
        num_jsons = len(list(level_path.glob('*.json')))
        print(f"  {level}/: {num_images} images, {num_jsons} JSON templates")


def main():
    # Use the latest Claude evaluation (which has all 27 diagrams)
    evaluation_dir = 'data/02_results/diagram_evaluations/claude_sonnet_4_5_20250929/eval_20251231_155722'
    output_base = 'data/03_ground_truth'

    setup_ground_truth(evaluation_dir, output_base)


if __name__ == '__main__':
    main()
