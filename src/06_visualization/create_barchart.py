#!/usr/bin/env python3
"""
Consolidated barchart creation utility for PIP Manuscripts Processor.
Replaces: barchart_by_diagram.py, barchart_by_page.py, draw_barchart.py

Usage:
    python create_barchart.py diagrams --input classified_pages.csv
    python create_barchart.py pages --input collection_metadata.json
    python create_barchart.py items --input collection_metadata.json
"""

import argparse
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties


def load_lato_font(fonts_dir="fonts"):
    """Load Lato font and set as default."""
    if not os.path.isdir(fonts_dir):
        print(f"⚠️ Font directory not found: {fonts_dir}, using default font")
        return None

    # Add all TTF files to font manager
    for fname in os.listdir(fonts_dir):
        if fname.lower().endswith(".ttf"):
            fm.fontManager.addfont(os.path.join(fonts_dir, fname))

    # Find Lato variants
    all_fonts = [f.name for f in fm.fontManager.ttflist]
    lato_variants = sorted({name for name in all_fonts if "lato" in name.lower()})

    if not lato_variants:
        print("⚠️ No Lato font variant loaded, using default font")
        return None

    chosen_font = lato_variants[0]
    mpl.rcParams["font.family"] = chosen_font
    print(f"✅ Using font: {chosen_font}")
    return FontProperties(family=chosen_font)


def create_diagrams_barchart(csv_path, output_dir, font_prop):
    """Create bar chart showing distribution of diagram-mixed pages by category."""
    df = pd.read_csv(csv_path)

    # Filter for diagram_mixed predictions under Manuscripts
    df = df[df["Predicted_Label"] == "diagram_mixed"]
    df = df[df["Category Level 1"].str.strip() == "I. Manuscripts"]
    df = df[df["Category Level 2"].notnull() & (df["Category Level 2"].str.strip() != "")]

    # Count diagrams by category
    counts = df.groupby("Category Level 2").size().sort_index()

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(counts))
    ax.bar(x, counts.values, color="#336699")

    # Annotate bars
    for i, val in enumerate(counts.values):
        ax.text(i, val + 0.5, str(val), ha="center", fontproperties=font_prop, fontsize=8)

    # Formatting
    ax.set_xticks(x)
    ax.set_xticklabels(counts.index, rotation=45, ha="right", fontproperties=font_prop)
    ax.set_title("Distribution of Diagram-Mixed Pages by Category (Robin Level 2)",
                 fontproperties=font_prop, fontsize=14)
    ax.set_xlabel("Category", fontproperties=font_prop)
    ax.set_ylabel("Diagram Pages", fontproperties=font_prop)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    output_path = os.path.join(output_dir, "diagram_distribution_by_category.png")
    plt.savefig(output_path, dpi=300)
    print(f"✅ Plot saved to: {output_path}")
    plt.close()


def create_pages_barchart(json_path, output_dir, font_prop):
    """Create bar chart showing page count distribution by category."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # Filter for Manuscripts only
    df = df[df["Category Level 1"].str.strip() == "I. Manuscripts"]
    df = df[df["Category Level 2"].notnull() & (df["Category Level 2"].str.strip() != "")]
    df["Page Count"] = pd.to_numeric(df["Page Count"], errors="coerce").fillna(0).astype(int)

    # Calculate total pages per category
    pages_by_cat = df.groupby("Category Level 2")["Page Count"].sum().sort_index()

    # Export CSV
    csv_path = os.path.join(output_dir, "pages_distribution.csv")
    pages_by_cat.to_frame(name="Total Pages").to_csv(csv_path)
    print(f"✅ CSV saved to: {csv_path}")

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(pages_by_cat))
    ax.bar(x, pages_by_cat.values)

    # Annotate bars
    for i, val in enumerate(pages_by_cat.values):
        ax.text(i, val + 1, str(val), ha="center", fontproperties=font_prop, fontsize=8)

    # Formatting
    ax.set_xticks(x)
    ax.set_xticklabels(pages_by_cat.index, rotation=45, ha="right", fontproperties=font_prop)
    ax.set_title("Page Count Distribution by Category (Level 2)",
                 fontproperties=font_prop, fontsize=14)
    ax.set_xlabel("Category", fontproperties=font_prop)
    ax.set_ylabel("Pages", fontproperties=font_prop)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    output_path = os.path.join(output_dir, "pages_distribution.png")
    plt.savefig(output_path, dpi=300)
    print(f"🖼️ Image saved to: {output_path} (300 dpi)")
    plt.close()


def create_items_barchart(json_path, output_dir, font_prop):
    """Create bar chart comparing total items vs digitized items by category."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # Filter for Manuscripts only
    df_manuscripts = df[df["Category Level 1"].str.strip() == "I. Manuscripts"]
    df_manuscripts = df_manuscripts[
        df_manuscripts["Category Level 2"].notnull() &
        (df_manuscripts["Category Level 2"].str.strip() != "")
    ]

    # Count totals and digitized
    total_counts = df_manuscripts["Category Level 2"].value_counts().sort_index()
    df_digital = df_manuscripts[
        df_manuscripts["Digital Link"].notnull() &
        (df_manuscripts["Digital Link"].str.strip() != "")
    ]
    digital_counts = df_digital["Category Level 2"].value_counts().sort_index()

    # Combine
    combined_counts = pd.DataFrame({
        "Total Items": total_counts,
        "Digitized Items": digital_counts
    }).fillna(0).astype(int)

    # Export CSV
    csv_path = os.path.join(output_dir, "category_distribution.csv")
    combined_counts.to_csv(csv_path)
    print(f"✅ CSV saved to: {csv_path}")

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    bar_width = 0.4
    x = range(len(combined_counts))

    ax.bar(x, combined_counts["Total Items"], width=bar_width,
           label="Total Items", color="#4063D8")
    ax.bar([i + bar_width for i in x], combined_counts["Digitized Items"],
           width=bar_width, label="Digitized Items", color="#389826")

    # Annotate values
    for i in x:
        ax.text(i, combined_counts["Total Items"].iloc[i] + 0.5,
                str(combined_counts["Total Items"].iloc[i]),
                ha="center", fontproperties=font_prop, fontsize=8)
        ax.text(i + bar_width, combined_counts["Digitized Items"].iloc[i] + 0.5,
                str(combined_counts["Digitized Items"].iloc[i]),
                ha="center", fontproperties=font_prop, fontsize=8)

    # Formatting
    ax.set_xticks([i + bar_width / 2 for i in x])
    ax.set_xticklabels(combined_counts.index, rotation=45, ha="right", fontproperties=font_prop)
    ax.set_title("Distribution of Manuscripts and Digitized Items by Category (Level 2)",
                 fontproperties=font_prop, fontsize=14)
    ax.set_xlabel("Category", fontproperties=font_prop)
    ax.set_ylabel("Number of Items", fontproperties=font_prop)
    ax.legend(prop=font_prop)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    output_path = os.path.join(output_dir, "category_distribution.png")
    plt.savefig(output_path, dpi=300)
    print(f"🖼️ Image saved to: {output_path} (300 dpi)")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Create bar charts for PIP Manuscripts Processor visualizations"
    )
    subparsers = parser.add_subparsers(dest="chart_type", help="Chart type")

    # Diagrams subcommand
    parser_diagrams = subparsers.add_parser(
        "diagrams",
        help="Create diagram distribution chart from classified pages CSV"
    )
    parser_diagrams.add_argument(
        "--input",
        default="../../data/results/classified_pages.csv",
        help="Path to classified_pages.csv"
    )
    parser_diagrams.add_argument(
        "--output",
        default="../../data/visualizations",
        help="Output directory"
    )
    parser_diagrams.add_argument(
        "--fonts-dir",
        default="fonts",
        help="Directory containing Lato font files"
    )

    # Pages subcommand
    parser_pages = subparsers.add_parser(
        "pages",
        help="Create page count distribution chart from collection metadata JSON"
    )
    parser_pages.add_argument(
        "--input",
        default="collection_metadata.json",
        help="Path to collection_metadata.json"
    )
    parser_pages.add_argument(
        "--output",
        default="./",
        help="Output directory"
    )
    parser_pages.add_argument(
        "--fonts-dir",
        default="fonts",
        help="Directory containing Lato font files"
    )

    # Items subcommand
    parser_items = subparsers.add_parser(
        "items",
        help="Create items distribution chart (total vs digitized) from collection metadata JSON"
    )
    parser_items.add_argument(
        "--input",
        default="collection_metadata.json",
        help="Path to collection_metadata.json"
    )
    parser_items.add_argument(
        "--output",
        default="visualizations",
        help="Output directory"
    )
    parser_items.add_argument(
        "--fonts-dir",
        default="fonts",
        help="Directory containing Lato font files"
    )

    args = parser.parse_args()

    if not args.chart_type:
        parser.print_help()
        return

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Load font
    font_prop = load_lato_font(args.fonts_dir)

    # Create appropriate chart
    if args.chart_type == "diagrams":
        create_diagrams_barchart(args.input, args.output, font_prop)
    elif args.chart_type == "pages":
        create_pages_barchart(args.input, args.output, font_prop)
    elif args.chart_type == "items":
        create_items_barchart(args.input, args.output, font_prop)


if __name__ == "__main__":
    main()
