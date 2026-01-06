# VLM Evaluation Prompts - Peirce Existential Graphs

Three-tier evaluation framework based on Peirce's semiotic categories (Firstness, Secondness, Thirdness)

---

## 1. MORPHOLOGICAL PROMPT (Firstness)

**Purpose**: Element enumeration - counting visual components without interpretation

```
OUTPUT FORMAT: JSON only, no explanation.

Count visual elements in this diagram:
1. Cuts (closed curves): How many?
2. Lines (heavy lines): How many? Do any branch?
3. Spots (text labels): How many? What text?

JSON:
{"cuts":{"count":N,"nested":true/false},"lines":{"count":N,"branching":true/false},"spots":{"count":N,"labels":["..."]}}
```

**Evaluation Method**: JSON exact-match
**Metrics**: Count-based precision/recall

---

## 2. INDEXICAL PROMPT (Secondness)

**Purpose**: Spatial relationships - describing topological structure without logical interpretation

```
Describe the spatial relationships in this diagram.

CONTAINMENT: Which text labels are inside or outside each closed curve?
CONNECTIONS: Which text labels are connected by lines? Note any branching or unconnected lines.
BOUNDARY CROSSINGS: Do any lines cross the boundaries of closed curves?
NESTING: Are any closed curves nested inside others?

Do not interpret meaning. Only describe what you see spatially.
```

**Evaluation Method**: LLM-as-judge
**Focus**: Topological accuracy, spatial precision

---

## 3. SYMBOLIC PROMPT (Thirdness)

**Purpose**: Logical interpretation - translating diagram to natural language using Peirce's rules

```
EXISTENTIAL GRAPH INTERPRETATION

Analyze this Peirce Existential Graph and provide its logical reading in natural language.

=== COMPONENTS ===
- TEXT LABELS (spots): predicates ("man", "wounded", "adores")
- HEAVY LINES: connect spots, represent same individual
- CLOSED CURVES (cuts): negation - deny everything inside
- BRANCHING LINES: same individual with multiple predicates

=== QUANTIFICATION ===
Count how many cuts enclose the OUTERMOST part of each line:
- EVEN (0,2,4...): "some", "there exists" (∃)
- ODD (1,3,5...): "every", "all" (∀)

=== KEY PATTERNS ===

1. Line on sheet (0 cuts): "Something is X"
2. Line in 1 cut: "Nothing is X"
3. Line crossing cut outward: "Some X is not Y"
4. Scroll (nested cuts, line at 1 cut): "Every X is Y"
5. Two lines, different depths: scope determined by outermost position

=== READING EXAMPLES ===

man──wounded (in one cut)
→ "No man is wounded"

man────┬──wounded (man outside, wounded in cut)
→ "Some man is not wounded"

man────wounded (both in nested cuts, line at 1 cut)
→ "Every man is wounded"

Catholic──adores──woman (Catholic in cuts, woman outside)
→ "Some woman is adored by every Catholic"

man──┬──rational (in scroll structure)
     └──animal
→ "Every man is rational and animal"

=== TASK ===
Provide the natural language reading. Be precise about quantifiers and negation scope.
```

**Evaluation Method**: LLM-as-judge
**Focus**: Logical correctness, quantifier accuracy, scope interpretation

---

## Dataset

- **Total diagrams**: 27
- **Source**: Peirce MS (Houghton) hou02614c00458 - "D. Logic"
- **Pages**: seq13, seq15, seq617, seq621, seq625

## Models Evaluated

1. Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
2. Gemini 3 Pro Preview (google/gemini-3-pro-preview)
3. Gemini 3 Flash Preview (google/gemini-3-flash-preview)
4. Gemma 3 27B IT (gemma-3-27b-it)
5. Qwen 2.5 VL 72B Instruct (qwen2.5-vl-72b-instruct)

**Total evaluations**: 405 (27 diagrams × 5 models × 3 levels)
