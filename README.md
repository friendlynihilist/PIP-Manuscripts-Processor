# PIP-Manuscripts-Processor

**PIP-Manuscripts-Processor** is a modular preprocessing and analysis pipeline developed within the *Peirce Interprets Peirce* project.  
It enables structured access to the digitised manuscripts of Charles S. Peirce and supports downstream tasks such as visual classification, diagram recognition, and semantic annotation.

## Features

- Extracts structured metadata from Harvard’s Houghton Library IIIF manifests
- Downloads and organises manuscript pages by Robin’s classification system
- Identifies and classifies manuscript pages into `text`, `diagram_mixed`, and `cover`
- Computes CLIP embeddings for all pages to support downstream ML tasks
- Generates derivative datasets (e.g. only diagram-rich pages) for layout detection
- Provides UMAP visualisation for interpretability and quality control
- Prepares outputs for semantic reinjection into IIIF using `oa:Annotation`

## Installation

```bash
git clone https://github.com/friendlynihilist/PIP-Manuscripts-Processor.git
cd PIP-Manuscripts-Processor
pip install -r requirements.txt
```

## Usage

Example: extract CLIP embeddings for the full corpus:

```bash
python src/features/generate_clip_embeddings_full.py
```

Run the classification pipeline on training/test sets:

```bash
python src/classification/train_logistic_clip.py
```

Generate UMAP plots from CLIP vectors and Robin categories:

```bash
python src/visualisation/umap_diagram_by_category.py
```

## Folder Structure

- `data/raw/Manuscripts/`: original image files, organised by category and item ID
- `data/processed/`: metadata files, CSVs, embeddings, classification results
- `data/derived/`: generated subsets, e.g. layout-ready diagram pages
- `src/`: all scripts grouped by function (`features`, `classification`, `visualisation`, `layout`)

## License

MIT License