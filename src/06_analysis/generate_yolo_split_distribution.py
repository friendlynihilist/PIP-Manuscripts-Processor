#!/usr/bin/env python3
"""
Generate dataset split distribution for YOLO after augmentation.
Shows train/validation split with annotation counts.
"""

from pathlib import Path
import pandas as pd
from collections import defaultdict


def count_annotations_in_file(label_path):
    """Count annotations by class in a YOLO label file."""
    class_counts = defaultdict(int)

    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                # Parse as float first, then convert to int
                class_id = int(float(parts[0]))
                class_counts[class_id] += 1

    return class_counts


def analyze_split(split_dir, split_name):
    """Analyze a dataset split directory."""
    label_files = list(split_dir.glob('*.txt'))

    stats = {
        'split': split_name,
        'num_images': len(label_files),
        'num_diagram_annotations': 0,
        'num_textblock_annotations': 0
    }

    for label_file in label_files:
        counts = count_annotations_in_file(label_file)
        stats['num_diagram_annotations'] += counts.get(0, 0)  # class 0 = diagram
        stats['num_textblock_annotations'] += counts.get(1, 0)  # class 1 = text_block

    return stats


def main():
    # Paths to train and validation directories
    train_dir = Path('data/01_intermediate/yolo_detections/labels/train')
    val_dir = Path('data/01_intermediate/yolo_detections/labels/val')

    print("Analyzing YOLO dataset splits (after augmentation)...")

    # Analyze each split
    train_stats = analyze_split(train_dir, 'train')
    val_stats = analyze_split(val_dir, 'validation')

    # Create results list
    results = [train_stats, val_stats]

    # Create DataFrame
    output_df = pd.DataFrame(results)

    # Save to CSV
    output_path = 'yolo_split_distribution.csv'
    output_df.to_csv(output_path, index=False)

    print(f"\n✅ Split distribution saved to: {output_path}")

    # Display results
    print(f"\n=== YOLO Dataset Split Distribution (After Augmentation) ===")
    print(output_df.to_string(index=False))

    # Calculate totals and percentages
    total_images = train_stats['num_images'] + val_stats['num_images']
    total_diagrams = train_stats['num_diagram_annotations'] + val_stats['num_diagram_annotations']
    total_textblocks = train_stats['num_textblock_annotations'] + val_stats['num_textblock_annotations']

    print(f"\n=== Summary ===")
    print(f"Total images: {total_images}")
    print(f"Train split: {train_stats['num_images']} ({train_stats['num_images']/total_images*100:.1f}%)")
    print(f"Val split: {val_stats['num_images']} ({val_stats['num_images']/total_images*100:.1f}%)")
    print(f"\nTotal diagram annotations: {total_diagrams}")
    print(f"Total text_block annotations: {total_textblocks}")
    print(f"Total annotations: {total_diagrams + total_textblocks}")

    # Show average annotations per image
    print(f"\n=== Average Annotations per Image ===")
    print(f"Train - Diagrams: {train_stats['num_diagram_annotations']/train_stats['num_images']:.2f}")
    print(f"Train - Text blocks: {train_stats['num_textblock_annotations']/train_stats['num_images']:.2f}")
    print(f"Val - Diagrams: {val_stats['num_diagram_annotations']/val_stats['num_images']:.2f}")
    print(f"Val - Text blocks: {val_stats['num_textblock_annotations']/val_stats['num_images']:.2f}")


if __name__ == '__main__':
    main()
