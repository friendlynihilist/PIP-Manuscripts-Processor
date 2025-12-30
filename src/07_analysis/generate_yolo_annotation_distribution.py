#!/usr/bin/env python3
"""
Generate distribution CSV for YOLO annotation dataset.
Analyzes the manually annotated images used for YOLOv8m training (before augmentation).
"""

from pathlib import Path
import pandas as pd
from collections import defaultdict


def parse_yolo_label_file(label_path):
    """Parse a YOLO format label file and return class counts."""
    class_counts = defaultdict(int)

    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                class_id = int(parts[0])
                class_counts[class_id] += 1

    return class_counts


def main():
    # YOLO class mapping
    class_names = {
        0: 'diagram',
        1: 'text_block'
    }

    # Find all original (non-augmented) label files
    train_dir = Path('data/01_intermediate/yolo_detections/labels/train')
    val_dir = Path('data/01_intermediate/yolo_detections/labels/val')

    # Get original files only (no _aug in filename)
    original_train_files = [f for f in train_dir.glob('*.txt') if '_aug' not in f.name]
    original_val_files = [f for f in val_dir.glob('*.txt') if '_aug' not in f.name]

    all_original_files = original_train_files + original_val_files

    print(f"Found {len(all_original_files)} manually annotated images (before augmentation)")
    print(f"  - Train: {len(original_train_files)}")
    print(f"  - Val: {len(original_val_files)}")

    # Initialize counters
    class_stats = {
        'diagram': {
            'images_with_class': 0,
            'total_annotations': 0
        },
        'text_block': {
            'images_with_class': 0,
            'total_annotations': 0
        }
    }

    # Process each file
    for label_file in all_original_files:
        class_counts = parse_yolo_label_file(label_file)

        for class_id, count in class_counts.items():
            class_name = class_names[class_id]
            class_stats[class_name]['images_with_class'] += 1
            class_stats[class_name]['total_annotations'] += count

    # Create output data
    results = []
    for class_name in ['diagram', 'text_block']:
        stats = class_stats[class_name]
        num_images = stats['images_with_class']
        num_annotations = stats['total_annotations']

        if num_images > 0:
            avg_per_image = num_annotations / num_images
        else:
            avg_per_image = 0.0

        results.append({
            'class': class_name,
            'num_images': num_images,
            'num_annotations': num_annotations,
            'avg_annotations_per_image': round(avg_per_image, 2)
        })

    # Create DataFrame
    output_df = pd.DataFrame(results)

    # Save to CSV
    output_path = 'yolo_annotation_distribution.csv'
    output_df.to_csv(output_path, index=False)

    print(f"\n✅ Distribution saved to: {output_path}")
    print(f"\n=== YOLO Annotation Distribution ===")
    print(output_df.to_string(index=False))

    # Print summary
    total_annotations = sum(r['num_annotations'] for r in results)
    total_images = len(all_original_files)
    print(f"\n=== Summary ===")
    print(f"Total images: {total_images}")
    print(f"Total annotations: {total_annotations}")
    print(f"Average annotations per image: {total_annotations / total_images:.2f}")

    # Also show augmented dataset size for reference
    all_train_files = list(train_dir.glob('*.txt'))
    all_val_files = list(val_dir.glob('*.txt'))
    print(f"\n=== After Augmentation ===")
    print(f"Train images: {len(all_train_files)}")
    print(f"Val images: {len(all_val_files)}")
    print(f"Total augmented dataset: {len(all_train_files) + len(all_val_files)}")


if __name__ == '__main__':
    main()
