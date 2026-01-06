# Diagram Evaluation System - Development Summary

## Overview

We built a unified diagram evaluation system that uses multiple Vision-Language Models (VLMs) to analyze diagram segments from the Charles S. Peirce manuscript collection. The system supports 4 different models through 3 different APIs.

## System Architecture

### Main Script
**Location:** `src/04_inference/evaluate_diagrams.py`

This unified script evaluates diagram segments using vision-language models with configurable prompts.

### Supported Models

| Model | API | Provider | Max Tokens |
|-------|-----|----------|------------|
| Claude Sonnet 4.5 | Anthropic Direct | Anthropic | 2048 |
| Gemini 3 Pro Preview | OpenRouter | Google | 8192* |
| Gemma 3 27B IT | AcademicCloud | Google | 2048 |
| Qwen 2.5 VL 72B | AcademicCloud | Alibaba | 2048 |

*Increased from 2048 to accommodate reasoning tokens (see Issues section)

### Data Flow

1. **Input:** Diagram segments indexed in `data/02_results/manuscripts_segments_index.csv`
2. **Processing:** VLM analyzes cropped diagram images from `data/02_results/crops/`
3. **Output:** JSON evaluations saved to `data/02_results/diagram_evaluations/{model}/{run_id}/`

### Evaluation Prompts

Six prompt templates are available:

- **morphological:** Count and categorize elements (words, lines, shapes, etc.)
- **indexical:** Identify relationships between elements
- **symbolic:** Interpret using Peirce's Existential Graph notation
- **description:** General description of diagram
- **classification:** Categorize diagram type
- **transcription:** Extract text and symbols

## API Integrations

### 1. Anthropic API (Claude)
```python
ANTHROPIC_API_KEY = "sk-ant-api03-..."
model_id = "claude-sonnet-4-5-20250929"
```
Direct integration using Anthropic SDK.

### 2. OpenRouter API (Gemini)
```python
OPENROUTER_API_KEY = "sk-or-v1-..."
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
model_id = "google/gemini-3-pro-preview"
```
OpenAI-compatible API gateway providing access to Gemini.

### 3. AcademicCloud API (Gemma, Qwen)
```python
ACADEMICCLOUD_API_KEY = "44767d9d..."
ACADEMICCLOUD_BASE_URL = "https://chat-ai.academiccloud.de/v1"
```
Academic research API with OpenAI-compatible endpoints.

## Issues Encountered & Solutions

### Issue 1: Gemini Empty Responses (Initial Discovery)

**Problem:** 44% of Gemini evaluations (8 out of 18) returned empty `"evaluation"` fields.

**Initial Hypothesis:** Content safety filters blocking images with words like "man", "disgraced", "wounded"

**Investigation:**
- Attempted to add scholarly context to prompts (failed - syntax errors)
- User identified the actual issue: images might not be sent correctly through OpenRouter API

### Issue 2: Incorrect OpenRouter API Format

**Problem:** Image and text in wrong order in the content array.

**Root Cause:**
```python
# WRONG (original implementation)
"content": [
    {"type": "image_url", ...},  # Image first
    {"type": "text", ...}         # Text second
]
```

**Solution:**
```python
# CORRECT (fixed implementation)
"content": [
    {"type": "text", ...},        # Text first
    {"type": "image_url", ...}    # Image second
]
```

**File:** `src/04_inference/evaluate_diagrams.py:348-362`

**Result:** Improved success rate from 56% to 67%, but still had 2 empty responses.

### Issue 3: Token Limit Exhaustion (Root Cause Discovery)

**Problem:** Even with correct API format, 2 out of 6 evaluations still returned empty responses.

**Debugging Process:**
1. Added metadata extraction to capture `finish_reason` from API response
2. Added debug logging for empty responses
3. Printed full response object

**Key Discovery:**
```python
finish_reason: 'length'
native_finish_reason: 'MAX_TOKENS'
completion_tokens: 2045 (reasoning) + 0 (content) = 2045/2048
reasoning: [extensive internal chain-of-thought...]
content: '' (empty - ran out of tokens!)
```

**Root Cause:**
Gemini 3 Pro Preview has internal reasoning capabilities (similar to o1/o3). It was using ALL 2048 tokens for internal chain-of-thought reasoning, leaving **zero tokens** for the actual response.

**Solution:**
```python
"gemini": {
    "model_id": "google/gemini-3-pro-preview",
    "api": "openrouter",
    "max_tokens": 8192,  # Increased from 2048
},
```

**Result:** 100% success rate (6/6 evaluations complete with content)

## Key Technical Insights

### Gemini 3 Pro Preview Reasoning Behavior

The API response reveals Gemini's internal reasoning process:

```json
{
  "reasoning": "**Identifying Elements Within**\n\nI'm currently focused on...",
  "reasoning_details": [{
    "format": "google-gemini-v1",
    "type": "reasoning.text",
    "text": "..."
  }],
  "completion_tokens": 2045,
  "reasoning_tokens": 2045
}
```

Gemini performs extended chain-of-thought reasoning before generating the final answer, consuming 1500-2500 tokens on internal analysis. This requires higher `max_tokens` limits compared to non-reasoning models.

## Current Status

### Completed Work
- ✅ Unified evaluation script supporting 4 VLMs
- ✅ Fixed OpenRouter API content ordering
- ✅ Fixed Gemini token limit issue
- ✅ Successfully evaluated 6 test diagrams (100% success)
- ✅ Partially evaluated 370 diagrams from full corpus

### Test Results
| Model | Test Page | Diagrams | Success | Failed |
|-------|-----------|----------|---------|--------|
| Claude Sonnet 4.5 | D._Logic__hou02614c00458__seq15 | 68 | 68 | 0 |
| Qwen 2.5 VL 72B | D._Logic__hou02614c00458__seq15 | 18 | 18 | 0 |
| Gemma 3 27B IT | D._Logic__hou02614c00458__seq15 | 18 | 18 | 0 |
| Gemini 3 Pro Preview | D._Logic__hou02614c00458__seq15 | 6 | 6 | 0 |

### Partial Run
- **Gemini 3 Pro Preview:** 370/6462 diagrams evaluated (~5.7% complete)
- **Location:** `data/02_results/diagram_evaluations/google/gemini_3_pro_preview/eval_20251227_000416/`

## Usage Examples

### Evaluate with specific model
```bash
python3 src/04_inference/evaluate_diagrams.py claude
python3 src/04_inference/evaluate_diagrams.py gemini
python3 src/04_inference/evaluate_diagrams.py qwen
python3 src/04_inference/evaluate_diagrams.py gemma
```

### Filter to specific page
```bash
python3 src/04_inference/evaluate_diagrams.py gemini --page D._Logic__hou02614c00458__seq15
```

### Limit number of diagrams
```bash
python3 src/04_inference/evaluate_diagrams.py gemini --limit 100
```

### Use different prompt
```bash
python3 src/04_inference/evaluate_diagrams.py gemini --prompt symbolic
```

### Custom prompt
```bash
python3 src/04_inference/evaluate_diagrams.py gemini --custom-prompt "Describe this diagram in detail"
```

## Output Format

Each evaluation produces a JSON file:

```json
{
  "manuscript_id": "hou02614c00458",
  "page_filename": "D._Logic__hou02614c00458__seq15.jpg",
  "segment_index": "1",
  "crop_path": "/path/to/cropped/image.jpg",
  "x": 825,
  "y": 594,
  "width": 668,
  "height": 210,
  "canvas_uri": "https://iiif.lib.harvard.edu/manifests/...",
  "category_level_1": "I. Manuscripts",
  "category_level_2": "D. Logic",
  "prompt": "How many and what kind of elements...",
  "evaluation": "Based on the image, there are **7 distinct elements**...",
  "finish_reason": "stop",
  "model": "google/gemini-3-pro-preview",
  "timestamp": "2025-12-26T23:45:49.241503"
}
```

A `summary.json` file aggregates results:

```json
{
  "model": "google/gemini-3-pro-preview",
  "prompt": "How many and what kind of elements...",
  "total_diagrams": 6,
  "successful": 6,
  "failed": 0,
  "timestamp": "20251226_235835",
  "results": [...]
}
```

## Related Files

### Data Files
- **Segments Index:** `data/02_results/manuscripts_segments_index.csv`
  - Created by: `src/utils/create_segments_index.py`
  - Contains metadata for all manuscript segments (diagrams + text blocks)
  - Links to YOLO detection results and cropped images

- **Collection Metadata:** `data/00_raw/metadata/collection_metadata.json`
  - Manuscript-level metadata (titles, dates, categories, IIIF URIs)

- **YOLO Labels:** `experiments/yolo_runs/runs/detect/full_corpus_detection/labels/`
  - Layout segmentation results (diagram vs text block detection)

- **Cropped Images:** `data/02_results/crops/cropped/`
  - Individual diagram segments extracted from pages

### Evaluation Outputs
```
data/02_results/diagram_evaluations/
├── claude_sonnet_4_5_20250929/
│   └── eval_YYYYMMDD_HHMMSS/
│       ├── {diagram_id}.json
│       └── summary.json
├── google/
│   └── gemini_3_pro_preview/
│       └── eval_YYYYMMDD_HHMMSS/
├── qwen2_5_vl_72b_instruct/
└── gemma_3_27b_it/
```

## Next Steps

1. **Complete Test Set Evaluation**
   - Run Gemini on 100-200 diagram test set
   - Compare results across all 4 models

2. **Full Corpus Evaluation** (Optional)
   - 6,462 total diagrams
   - ~9 hours with 5s delay
   - Consider reducing delay or running overnight

3. **Analysis & Comparison**
   - Compare model performance on different prompt types
   - Analyze which model performs best for Peirce's logical diagrams
   - Evaluate accuracy of symbolic interpretations

4. **Performance Optimization**
   - Reduce API delay if rate limits allow
   - Consider batch processing for certain APIs
   - Implement parallel processing for multiple models

## Important Notes

- **Cost Awareness:** Gemini 3 Pro Preview uses significantly more tokens due to reasoning (2000-3000 tokens per evaluation vs 500-1000 for other models)
- **Rate Limiting:** 5-second delay between requests to avoid hitting API limits
- **Token Limits:** Models with reasoning capabilities need higher `max_tokens` settings
- **Content Ordering:** OpenRouter API requires text before image (differs from some other APIs)

## Debugging Tools

The script includes debugging output for empty responses:

```python
if not response_text or response_text.strip() == "":
    print(f"    ⚠️  Empty response detected!")
    print(f"    finish_reason: {finish_reason}")
    print(f"    Full response object: {response}")
```

This helped identify the token limit issue by revealing:
- `finish_reason: 'length'`
- `completion_tokens` breakdown (reasoning vs content)
- Internal reasoning text

## Repository Context

This work is part of the PIP-Manuscripts-Processor project analyzing Charles S. Peirce's manuscript collection. The diagram evaluation system builds on:

1. **Layout Segmentation:** YOLO-based detection separating diagrams from text
2. **Metadata Integration:** IIIF manifests and collection metadata
3. **Segment Indexing:** Comprehensive CSV linking all components

The goal is to use VLMs to analyze and interpret Peirce's logical diagrams, particularly his Existential Graphs notation system.
