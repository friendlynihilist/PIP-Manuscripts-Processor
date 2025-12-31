#!/usr/bin/env python3
"""
Find missing diagram evaluations for each model.
"""

from pathlib import Path

# Expected diagram IDs (27 total)
EXPECTED_DIAGRAMS = [
    "hou02614c00458_D._Logic__hou02614c00458__seq13_0",
    "hou02614c00458_D._Logic__hou02614c00458__seq13_1",
    "hou02614c00458_D._Logic__hou02614c00458__seq15_0",
    "hou02614c00458_D._Logic__hou02614c00458__seq15_1",
    "hou02614c00458_D._Logic__hou02614c00458__seq15_3",
    "hou02614c00458_D._Logic__hou02614c00458__seq15_8",
    "hou02614c00458_D._Logic__hou02614c00458__seq15_12",
    "hou02614c00458_D._Logic__hou02614c00458__seq15_14",
    "hou02614c00458_D._Logic__hou02614c00458__seq617_0",
    "hou02614c00458_D._Logic__hou02614c00458__seq617_1",
    "hou02614c00458_D._Logic__hou02614c00458__seq617_2",
    "hou02614c00458_D._Logic__hou02614c00458__seq617_4",
    "hou02614c00458_D._Logic__hou02614c00458__seq621_0",
    "hou02614c00458_D._Logic__hou02614c00458__seq621_1",
    "hou02614c00458_D._Logic__hou02614c00458__seq621_2",
    "hou02614c00458_D._Logic__hou02614c00458__seq621_3",
    "hou02614c00458_D._Logic__hou02614c00458__seq621_4",
    "hou02614c00458_D._Logic__hou02614c00458__seq621_5",
    "hou02614c00458_D._Logic__hou02614c00458__seq625_0",
    "hou02614c00458_D._Logic__hou02614c00458__seq625_1",
    "hou02614c00458_D._Logic__hou02614c00458__seq625_2",
    "hou02614c00458_D._Logic__hou02614c00458__seq625_3",
    "hou02614c00458_D._Logic__hou02614c00458__seq625_4",
    "hou02614c00458_D._Logic__hou02614c00458__seq625_5",
    "hou02614c00458_D._Logic__hou02614c00458__seq625_6",
    "hou02614c00458_D._Logic__hou02614c00458__seq625_7",
    "hou02614c00458_D._Logic__hou02614c00458__seq625_9",
]

MODELS = {
    "Claude Sonnet 4.5": "claude_sonnet_4_5_20250929/eval_20251231_155722",
    "Gemini 3 Pro": "google/gemini_3_pro_preview/eval_20251231_155724",
    "Gemini 3 Flash": "google/gemini_3_flash_preview/eval_20251231_162141",
    "Gemma 3 27B": "gemma_3_27b_it/eval_20251231_155725",
    "Qwen 2.5 VL 72B": "qwen2_5_vl_72b_instruct/eval_20251231_155726",
}

def main():
    base_dir = Path("data/02_results/diagram_evaluations")

    print("=" * 70)
    print("MISSING DIAGRAM EVALUATIONS")
    print("=" * 70)
    print()

    all_missing = {}

    for model_name, eval_path in MODELS.items():
        eval_dir = base_dir / eval_path

        if not eval_dir.exists():
            print(f"{model_name}: Evaluation directory not found")
            continue

        # Get existing evaluations
        existing = set()
        for json_file in eval_dir.glob("*.json"):
            if json_file.name != "summary.json":
                existing.add(json_file.stem)

        # Find missing
        expected = set(EXPECTED_DIAGRAMS)
        missing = expected - existing

        print(f"{model_name}:")
        print(f"  Completed: {len(existing)}/27")

        if missing:
            print(f"  Missing ({len(missing)}):")
            for diagram_id in sorted(missing):
                print(f"    - {diagram_id}")
            all_missing[model_name] = sorted(missing)
        else:
            print(f"  ✓ Complete!")
        print()

    return all_missing

if __name__ == "__main__":
    main()
