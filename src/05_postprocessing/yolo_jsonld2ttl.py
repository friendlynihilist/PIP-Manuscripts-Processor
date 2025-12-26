from rdflib import Graph

# Load JSON-LD annotations
with open("yolo_layout_annotations.jsonld", "r", encoding="utf-8") as f:
    jsonld_data = f.read()

# Parse into RDF graph
g = Graph()
g.parse(data=jsonld_data, format="json-ld")

# Serialize to Turtle
output_file = "yolo_layout_annotations.ttl"
g.serialize(destination=output_file, format="turtle")

print(f"✅ Turtle serialization written to {output_file}")
print(f"📊 Total triples: {len(g)}")
