from rdflib import Graph

# Load JSON-LD annotations
with open("mlao_annotations.jsonld", "r", encoding="utf-8") as f:
    jsonld_data = f.read()

# Parse into RDF graph
g = Graph()
g.parse(data=jsonld_data, format="json-ld")

# Serialize to Turtle
g.serialize(destination="mlao_annotations.ttl", format="turtle")

print("Turtle serialization written to mlao_annotations.ttl")