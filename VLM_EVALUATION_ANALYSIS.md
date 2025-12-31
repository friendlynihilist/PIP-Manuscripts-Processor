# VLM Morphological Evaluation Analysis

## Overview

This document summarizes the comparative analysis of four Vision-Language Models (VLMs) on morphological diagram analysis of Charles Sanders Peirce's Existential Graphs.

## Evaluation Details

**Dataset**: 27 diagram segments from manuscript hou02614c00458
- Pages analyzed: seq13 (2 diagrams), seq15 (6 diagrams), seq617 (4 diagrams), seq621 (6 diagrams), seq625 (9 diagrams)

**Models Evaluated**:
1. **Claude Sonnet 4.5** (claude-sonnet-4-5-20250929)
2. **Gemini 3 Pro Preview** (google/gemini-3-pro-preview)
3. **Gemma 3 27B IT** (gemma-3-27b-it)
4. **Qwen 2.5 VL 72B Instruct** (qwen2.5-vl-72b-instruct)

**Evaluation Prompt**:
```
OUTPUT FORMAT: JSON only, no explanation.

Count visual elements in this diagram:
1. Cuts (closed curves): How many?
2. Lines (heavy lines): How many? Do any branch?
3. Spots (text labels): How many? What text?

JSON:
{"cuts":{"count":N,"nested":true/false},"lines":{"count":N,"branching":true/false},"spots":{"count":N,"labels":["..."]}}
```

## Model Completion Rates

| Model | Successful | Failed | Success Rate |
|-------|-----------|--------|--------------|
| Claude Sonnet 4.5 | 27/27 | 0 | 100.0% |
| Gemini 3 Pro | 25/27 | 2 (timeouts) | 92.6% |
| Gemma 3 27B | 24/27 | 3 (rate limits) | 88.9% |
| Qwen 2.5 VL 72B | 21/27 | 6 (rate limits) | 77.8% |

## Inter-Model Agreement

Agreement measured as percentage of diagrams where all models that successfully evaluated the diagram reported the same count.

| Metric | Agreements | Total Diagrams | Agreement Rate |
|--------|-----------|---------------|----------------|
| **Cuts count** | 12 | 27 | **44.4%** |
| **Lines count** | 4 | 27 | **14.8%** |
| **Spots count** | 9 | 27 | **33.3%** |

**Key Finding**: Only **2 out of 27 diagrams** (7.4%) showed perfect agreement across all three morphological features.

## Disagreement Analysis

**25 out of 27 diagrams** (92.6%) exhibited at least one type of disagreement across models.

### Common Disagreement Patterns

1. **Lines Count Variability** (highest disagreement: 85.2%)
   - Models frequently disagree on whether segments are distinct lines or parts of branching structures
   - Example (seq15_0): Claude/Gemini: 1 line, Qwen: 2 lines, Gemma: 3 lines

2. **Spots Count Differences** (66.7% disagreement)
   - Variation in text label identification and parsing
   - Some models combine compound labels (e.g., "man disgraced") while others separate them

3. **Cuts Count Variation** (55.6% disagreement)
   - Moderate disagreement on nested vs. separate closed curves
   - Example (seq625_2): Claude/Gemini: 4 cuts, Gemma: 3 cuts, Qwen: 2 cuts

## Example Case Study: seq15_0

This diagram demonstrates typical inter-model variation:

| Model | Cuts | Lines | Spots | Spot Labels |
|-------|------|-------|-------|-------------|
| Claude Sonnet 4.5 | 2 (nested) | 1 (branching) | 3 | man, disgraced, wounded |
| Gemini 3 Pro | 2 (nested) | 1 (branching) | 3 | man, man disgraced, wounded |
| Gemma 3 27B | 2 (nested) | 3 (branching) | 3 | man, manglisgrace, wounded |
| Qwen 2.5 VL 72B | 2 (nested) | 2 (branching) | 3 | man, disgraced, wounded |

**Analysis**: All models agree on cuts count and nesting, but disagree on lines (1-3) and show variation in label parsing.

## Implications

1. **Task Complexity**: Morphological analysis of Peirce's diagrams is challenging for current VLMs, with no model achieving consistent cross-validation with others.

2. **Lines Detection Challenge**: The low agreement (14.8%) on lines counting suggests this is the most difficult feature to analyze, likely due to:
   - Ambiguity in distinguishing connected vs. separate lines
   - Variation in branching structure interpretation
   - Difficulty parsing hand-drawn, historical manuscript imagery

3. **Model Reliability**: Claude Sonnet 4.5 achieved 100% completion rate, suggesting better robustness for this task, though agreement rates indicate all models interpret features differently.

4. **Ground Truth Need**: The high disagreement rates (55-85%) emphasize the need for manual ground truth annotations to evaluate which model performs most accurately.

## Data Files

Generated analysis files in `data/02_results/statistics/`:

1. **vlm_evaluation_summary.csv** - Overall agreement statistics
2. **vlm_evaluation_comparison.csv** - Per-diagram agreement analysis
3. **vlm_evaluation_detailed.csv** - Complete results matrix (all models × all diagrams)

Raw evaluation JSON files in `data/02_results/diagram_evaluations/[model]/eval_[timestamp]/`

## Methodology

Analysis performed using `src/07_analysis/compare_vlm_evaluations.py`, which:
- Loads all model evaluation JSON outputs
- Extracts structured counts from JSON responses
- Computes per-feature agreement rates
- Identifies specific disagreements for error analysis

---

**Date**: December 31, 2025
**Analyst**: Automated VLM evaluation pipeline
**Manuscript Source**: Harvard University, Houghton Library (MS Am 1632)
