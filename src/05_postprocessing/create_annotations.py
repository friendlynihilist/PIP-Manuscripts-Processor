import json
import uuid

# Load the evaluation data
with open("evaluation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

annotations = []

for diagram_id, content in data.items():
    metadata = content["metadata"]
    evaluations = content["evaluations"]
    manuscript_id = metadata["ID Manuscript"]
    canvas_uri = metadata["Canvas URI"]
    xywh = metadata["oa:Target"]

    for eval in evaluations:
        model_name = eval["model"]
        answers = eval["answers"]

        for category, answer in answers.items():
            # Determine conceptual category
            if category.startswith("Morphological"):
                conceptual_category = "pip:MorphologicalLevel"
            elif category.startswith("Indexical"):
                conceptual_category = "pip:IndexicalLevel"
            elif category.startswith("Symbolic"):
                conceptual_category = "pip:SemioticLevel"
            else:
                continue

            annotation = {
                "@context": [
                    "http://www.w3.org/ns/anno.jsonld",
                    {
                        "mlao": "https://w3id.org/mlao/ontology/",
                        "pip": "https://w3id.org/mlao/pip/",
                        "hico": "https://w3id.org/spar/hico/",
                        "prov": "http://www.w3.org/ns/prov#",
                        "oa": "http://www.w3.org/ns/oa#"
                    }
                ],
                "id": f"urn:uuid:{str(uuid.uuid4())}",
                "type": "Annotation",
                "motivation": "commenting",
                "body": {
                    "type": "TextualBody",
                    "value": answer,
                    "format": "text/plain"
                },
                "target": {
                    "source": canvas_uri,
                    "selector": {
                        "type": "FragmentSelector",
                        "conformsTo": "http://www.w3.org/TR/media-frags/",
                        "value": xywh
                    }
                },
                "mlao:isAnchoredTo": f"https://purl.org/peirce/manuscript/{manuscript_id}",
                "mlao:hasConceptualCategory": conceptual_category,
                "hico:hasInterpretationType": {
                    "id": f"https://w3id.org/mlao/vocab/{conceptual_category.split(':')[1]}Interpretation",
                    "type": "hico:InterpretationType"
                },
                "prov:wasGeneratedBy": {
                    "id": f"https://replicate.com/{model_name}",
                    "type": "prov:Activity",
                    "prov:type": "mlao:VisualLanguageModelEvaluation"
                }
            }

            annotations.append(annotation)

# Save all annotations to JSON-LD
with open("mlao_annotations.jsonld", "w", encoding="utf-8") as f:
    json.dump(annotations, f, indent=2)