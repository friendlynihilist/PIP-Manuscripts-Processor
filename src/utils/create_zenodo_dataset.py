#!/usr/bin/env python3
"""
Create Zenodo dataset with all relevant files for publication.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime


def create_jsonld():
    """Create JSON-LD file combining all ground truth annotations."""

    # Load all ground truth files
    with open('data/03_ground_truth/ground_truth_morphological.json', 'r') as f:
        morphological = json.load(f)

    with open('data/03_ground_truth/ground_truth_indexical.json', 'r') as f:
        indexical = json.load(f)

    with open('data/03_ground_truth/ground_truth_symbolic.json', 'r') as f:
        symbolic = json.load(f)

    # Create combined annotations
    diagrams = []
    for i, morph_diagram in enumerate(morphological['diagrams']):
        diagram_id = morph_diagram['diagram_id']

        # Find corresponding indexical and symbolic entries
        index_diagram = next((d for d in indexical['diagrams'] if d['diagram_id'] == diagram_id), None)
        symb_diagram = next((d for d in symbolic['diagrams'] if d['diagram_id'] == diagram_id), None)

        diagram = {
            "@type": "ExistentialGraphDiagram",
            "@id": f"urn:peirce:diagram:{diagram_id}",
            "diagram_id": diagram_id,
            "source_manuscript": "hou02614c00458",
            "source_collection": "Houghton Library, Harvard University",
            "annotations": {
                "morphological": {
                    "@type": "MorphologicalAnnotation",
                    "cuts": morph_diagram.get('cuts'),
                    "lines": morph_diagram.get('lines'),
                    "spots": morph_diagram.get('spots')
                },
                "indexical": {
                    "@type": "IndexicalAnnotation",
                    "description": index_diagram.get('indexical_description', '') if index_diagram else ''
                },
                "symbolic": {
                    "@type": "SymbolicAnnotation",
                    "reading": symb_diagram.get('symbolic_reading', '') if symb_diagram else ''
                }
            }
        }
        diagrams.append(diagram)

    # Create JSON-LD structure
    jsonld = {
        "@context": {
            "@vocab": "http://purl.org/peirce/existential-graphs#",
            "diagram_id": "identifier",
            "source_manuscript": "isPartOf",
            "source_collection": "repository",
            "cuts": "hasCuts",
            "lines": "hasLines",
            "spots": "hasSpots",
            "description": "spatialDescription",
            "reading": "logicalReading"
        },
        "@type": "Dataset",
        "@id": "urn:peirce:dataset:existential-graphs-vlm-evaluation",
        "name": "Peirce Existential Graphs - VLM Evaluation Dataset",
        "description": "Ground truth annotations for 27 Existential Graph diagrams from Peirce's manuscripts, annotated at three semiotic levels: morphological, indexical, and symbolic.",
        "creator": {
            "@type": "Person",
            "name": "Carlotta Opedretti"
        },
        "dateCreated": datetime.now().isoformat(),
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "keywords": ["Peirce", "Existential Graphs", "Logic", "Vision-Language Models", "Diagram Understanding"],
        "diagrams": diagrams,
        "statistics": {
            "total_diagrams": len(diagrams),
            "semiotic_levels": 3,
            "models_evaluated": 5
        }
    }

    return jsonld


def jsonld_to_turtle(jsonld_data):
    """Convert JSON-LD to Turtle format."""

    turtle = """@prefix eg: <http://purl.org/peirce/existential-graphs#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

<urn:peirce:dataset:existential-graphs-vlm-evaluation> a eg:Dataset ;
    dcterms:title "Peirce Existential Graphs - VLM Evaluation Dataset" ;
    dcterms:description "Ground truth annotations for 27 Existential Graph diagrams from Peirce's manuscripts, annotated at three semiotic levels: morphological, indexical, and symbolic." ;
    dcterms:creator "Carlotta Opedretti" ;
    dcterms:created "{date}"^^xsd:dateTime ;
    dcterms:license <https://creativecommons.org/licenses/by/4.0/> ;
    eg:totalDiagrams {total}^^xsd:integer ;
    eg:semioticLevels 3^^xsd:integer ;
    eg:modelsEvaluated 5^^xsd:integer .

""".format(
        date=datetime.now().isoformat(),
        total=len(jsonld_data['diagrams'])
    )

    # Add diagrams
    for diagram in jsonld_data['diagrams']:
        diagram_uri = diagram['@id']
        diagram_id = diagram['diagram_id']

        turtle += f"""
<{diagram_uri}> a eg:ExistentialGraphDiagram ;
    eg:identifier "{diagram_id}" ;
    dcterms:isPartOf "hou02614c00458" ;
    eg:repository "Houghton Library, Harvard University" .\n"""

        # Add morphological annotation
        morph = diagram['annotations']['morphological']
        if morph.get('cuts'):
            turtle += f"    eg:cutsCount {morph['cuts']['count']}^^xsd:integer ;\n"
            turtle += f"    eg:cutsNested {str(morph['cuts']['nested']).lower()}^^xsd:boolean ;\n"
        if morph.get('lines'):
            turtle += f"    eg:linesCount {morph['lines']['count']}^^xsd:integer ;\n"
            turtle += f"    eg:linesBranching {str(morph['lines']['branching']).lower()}^^xsd:boolean ;\n"
        if morph.get('spots'):
            turtle += f"    eg:spotsCount {morph['spots']['count']}^^xsd:integer ;\n"

    return turtle


def create_readme():
    """Create README for Zenodo dataset."""

    readme = """# Peirce Existential Graphs - VLM Evaluation Dataset

## Overview

This dataset contains ground truth annotations and model predictions for 27 Existential Graph diagrams from Charles Sanders Peirce's manuscripts, specifically from MS hou02614c00458 ("D. Logic") held at the Houghton Library, Harvard University.

The dataset supports the evaluation of Vision-Language Models (VLMs) on their ability to understand logical diagrams across three semiotic levels based on Peirce's categories.

## Dataset Structure

### Ground Truth Files

#### 1. `ground_truth_morphological.json`
**Semiotic Level**: Firstness
**Content**: Structural element counts (cuts, lines, spots)
**Format**: JSON with exact counts and boolean flags
**Evaluation Method**: Exact matching

Fields per diagram:
- `cuts`: Count and nesting information
- `lines`: Count and branching information
- `spots`: Count and text labels

#### 2. `ground_truth_indexical.json`
**Semiotic Level**: Secondness
**Content**: Spatial relationship descriptions
**Format**: Natural language annotations
**Evaluation Method**: LLM-as-judge

Describes:
- Containment relationships (which labels are inside/outside cuts)
- Line connections between predicates
- Boundary crossings
- Nesting structure

#### 3. `ground_truth_symbolic.json`
**Semiotic Level**: Thirdness
**Content**: Logical interpretations in natural language
**Format**: Natural language readings
**Evaluation Method**: LLM-as-judge

Provides the correct logical reading of each diagram following Peirce's rules for Existential Graphs.

### Model Predictions

#### 1. `morphological_predictions.json`
Consolidated predictions from 5 VLMs for morphological level (135 predictions: 27 diagrams × 5 models)

#### 2. `indexical_predictions.json`
Consolidated predictions from 5 VLMs for indexical level (135 predictions: 27 diagrams × 5 models)

#### 3. `symbolic_predictions.json`
Consolidated predictions from 5 VLMs for symbolic level (135 predictions: 27 diagrams × 5 models)

Each prediction includes:
- `diagram_id`: Unique identifier
- `model`: Model name
- `model_id`: Full model identifier
- `prediction`: Model's output
- `timestamp`: Evaluation timestamp

### Models Evaluated

1. **Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`)
2. **Gemini 3 Pro Preview** (`google/gemini-3-pro-preview`)
3. **Gemini 3 Flash Preview** (`google/gemini-3-flash-preview`)
4. **Gemma 3 27B IT** (`gemma-3-27b-it`)
5. **Qwen 2.5 VL 72B Instruct** (`qwen2.5-vl-72b-instruct`)

### Diagram Images

The `diagrams/` folder contains 27 JPG images, one for each annotated Existential Graph diagram extracted from the manuscript pages.

Naming convention: `hou02614c00458_D._Logic__hou02614c00458__seq{page}_{index}.jpg`

### Metadata Files

#### `manuscripts_segments_index.csv`
Complete index of all segmented elements from the manuscript, including:
- Page information
- Bounding box coordinates
- Segment class (diagram, text, etc.)
- Confidence scores

#### `dataset.jsonld`
JSON-LD representation of the complete dataset with semantic annotations following Linked Data principles.

#### `dataset.ttl`
RDF Turtle serialization of the dataset for semantic web applications.

#### `EVALUATION_PROMPTS.md`
Complete documentation of the three prompts used for VLM evaluation at each semiotic level.

## Dataset Statistics

- **Total Diagrams**: 27
- **Source Manuscript**: Peirce MS hou02614c00458
- **Source Pages**: seq13, seq15, seq617, seq621, seq625
- **Annotation Levels**: 3 (morphological, indexical, symbolic)
- **Models Evaluated**: 5
- **Total Predictions**: 405 (27 × 5 × 3)

## Semiotic Framework

The three-tier evaluation follows Peirce's phenomenological categories:

### Morphological (Firstness)
Pure visual qualities - counting elements without interpretation
- Evaluation: JSON exact-match
- Metrics: Precision, recall, F1 on element counts

### Indexical (Secondness)
Spatial relationships and topology
- Evaluation: LLM-as-judge comparing spatial descriptions
- Focus: Topological accuracy

### Symbolic (Thirdness)
Logical meaning and interpretation
- Evaluation: LLM-as-judge comparing logical readings
- Focus: Correct quantifiers, negation scope, logical form

## Usage

### Loading Ground Truth

```python
import json

# Load morphological ground truth
with open('ground_truth_morphological.json', 'r') as f:
    morphological_gt = json.load(f)

# Access a diagram's annotation
diagram = morphological_gt['diagrams'][0]
print(f"Diagram: {diagram['diagram_id']}")
print(f"Cuts: {diagram['cuts']['count']}")
print(f"Lines: {diagram['lines']['count']}")
print(f"Spots: {diagram['spots']['labels']}")
```

### Loading Predictions

```python
# Load all predictions for a level
with open('symbolic_predictions.json', 'r') as f:
    predictions = json.load(f)

# Filter predictions by model
claude_preds = [
    p for p in predictions['evaluations']
    if p['model'] == 'Claude Sonnet 4.5'
]
```

## Citation

If you use this dataset, please cite:

```
Opedretti, C. (2026). Peirce Existential Graphs - VLM Evaluation Dataset.
Zenodo. https://doi.org/[DOI]
```

## License

This dataset is released under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

You are free to:
- Share — copy and redistribute the material
- Adapt — remix, transform, and build upon the material

Under the following terms:
- Attribution — You must give appropriate credit

## Source

Original manuscript images are from the Charles Sanders Peirce Papers at Houghton Library, Harvard University.

## Contact

For questions or issues regarding this dataset, please contact: [Your contact information]

## Version History

- **v1.0** (2026-01-03): Initial release
  - 27 diagrams with three-level annotations
  - 405 VLM predictions from 5 models
  - Complete evaluation framework
"""

    return readme


def main():
    """Create Zenodo dataset folder with all files."""

    print("Creating Zenodo dataset...")

    # Create output directory
    zenodo_dir = Path("zenodo_dataset")
    zenodo_dir.mkdir(exist_ok=True)

    # 1. Create JSON-LD
    print("Creating JSON-LD...")
    jsonld_data = create_jsonld()
    with open(zenodo_dir / "dataset.jsonld", 'w', encoding='utf-8') as f:
        json.dump(jsonld_data, f, indent=2, ensure_ascii=False)

    # 2. Create Turtle/RDF
    print("Creating Turtle/RDF...")
    turtle_data = jsonld_to_turtle(jsonld_data)
    with open(zenodo_dir / "dataset.ttl", 'w', encoding='utf-8') as f:
        f.write(turtle_data)

    # 3. Create README
    print("Creating README...")
    readme_content = create_readme()
    with open(zenodo_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)

    # 4. Copy ground truth files
    print("Copying ground truth files...")
    shutil.copy2('data/03_ground_truth/ground_truth_morphological.json',
                 zenodo_dir / 'ground_truth_morphological.json')
    shutil.copy2('data/03_ground_truth/ground_truth_indexical.json',
                 zenodo_dir / 'ground_truth_indexical.json')
    shutil.copy2('data/03_ground_truth/ground_truth_symbolic.json',
                 zenodo_dir / 'ground_truth_symbolic.json')

    # 5. Copy prediction files
    print("Copying prediction files...")
    shutil.copy2('data/03_ground_truth/morphological_predictions.json',
                 zenodo_dir / 'morphological_predictions.json')
    shutil.copy2('data/03_ground_truth/indexical_predictions.json',
                 zenodo_dir / 'indexical_predictions.json')
    shutil.copy2('data/03_ground_truth/symbolic_predictions.json',
                 zenodo_dir / 'symbolic_predictions.json')

    # 6. Copy metadata files
    print("Copying metadata files...")
    shutil.copy2('data/02_results/manuscripts_segments_index.csv',
                 zenodo_dir / 'manuscripts_segments_index.csv')
    shutil.copy2('EVALUATION_PROMPTS.md',
                 zenodo_dir / 'EVALUATION_PROMPTS.md')

    # 7. Copy diagram images (just one copy)
    print("Copying diagram images...")
    diagrams_dir = zenodo_dir / "diagrams"
    diagrams_dir.mkdir(exist_ok=True)

    # Copy from morphological (they're all the same)
    source_diagrams = Path("data/03_ground_truth/morphological")
    for img_file in source_diagrams.glob("*.jpg"):
        shutil.copy2(img_file, diagrams_dir / img_file.name)

    print(f"\n✓ Zenodo dataset created in: {zenodo_dir}")
    print(f"  - {len(list(diagrams_dir.glob('*.jpg')))} diagram images")
    print(f"  - 6 prediction/ground truth JSON files")
    print(f"  - JSON-LD and Turtle metadata")
    print(f"  - README and documentation")
    print(f"\nTotal files: {len(list(zenodo_dir.rglob('*')))}")


if __name__ == "__main__":
    main()
