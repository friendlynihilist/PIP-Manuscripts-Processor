#!/usr/bin/env python3
"""
Consolidated counting utility for PIP Manuscripts Processor.
Replaces: count_images.py, count_items.py, count_labels.py

Usage:
    python count.py images <directory>
    python count.py items <json_file>
    python count.py labels <csv_file>
"""

import argparse
import csv
import json
import os
from collections import Counter


def count_images(root_dir, extensions=(".jpg", ".jpeg")):
    """Count image files in a directory tree."""
    total_count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        count = sum(1 for file in filenames if file.lower().endswith(extensions))
        total_count += count
    return total_count


def count_items(json_file_path):
    """Count manuscript items and pages from collection metadata JSON."""
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_items = 0
    digitized_items = 0
    total_pages = 0

    for item in data:
        series = item.get("Category Level 1") == "I. Manuscripts"
        subseries = item.get("Category Level 2")
        link = item.get("Digital Link", "")
        page_count = item.get("Page Count", 0)

        if series and subseries:
            total_items += 1
        if series and subseries and link:
            digitized_items += 1
        if series and subseries and isinstance(page_count, int):
            total_pages += page_count

    return {
        "total_items": total_items,
        "digitized_items": digitized_items,
        "total_pages": total_pages
    }


def count_labels(csv_file_path, label_column="Annotated Label"):
    """Count label occurrences in a CSV file."""
    label_counter = Counter()

    with open(csv_file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row.get(label_column, "").strip().lower()
            if label:
                label_counter[label] += 1

    return label_counter


def main():
    parser = argparse.ArgumentParser(
        description="Counting utilities for PIP Manuscripts Processor"
    )
    subparsers = parser.add_subparsers(dest="command", help="Count type")

    # Images subcommand
    parser_images = subparsers.add_parser("images", help="Count image files")
    parser_images.add_argument("directory", help="Root directory to search")
    parser_images.add_argument(
        "--extensions",
        nargs="+",
        default=[".jpg", ".jpeg"],
        help="Image file extensions (default: .jpg .jpeg)"
    )

    # Items subcommand
    parser_items = subparsers.add_parser("items", help="Count manuscript items and pages")
    parser_items.add_argument("json_file", help="Path to collection_metadata.json")

    # Labels subcommand
    parser_labels = subparsers.add_parser("labels", help="Count label occurrences")
    parser_labels.add_argument("csv_file", help="Path to CSV file with labels")
    parser_labels.add_argument(
        "--column",
        default="Annotated Label",
        help="Column name containing labels (default: 'Annotated Label')"
    )

    args = parser.parse_args()

    if args.command == "images":
        total = count_images(args.directory, tuple(args.extensions))
        print(f"📷 Total images in '{args.directory}': {total}")

    elif args.command == "items":
        counts = count_items(args.json_file)
        print(f"Total items (Manuscripts): {counts['total_items']}")
        print(f"Total digitized items (Manuscripts): {counts['digitized_items']}")
        print(f"Total pages for digitized items (Manuscripts): {counts['total_pages']}")

    elif args.command == "labels":
        label_counts = count_labels(args.csv_file, args.column)
        print("\n📊 Label Counts:")
        for label, count in label_counts.most_common():
            print(f" - {label}: {count}")
        print("\n✅ Done.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
