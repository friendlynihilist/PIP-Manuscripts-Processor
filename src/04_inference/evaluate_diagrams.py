#!/usr/bin/env python3
"""
Unified Diagram Evaluation Script
Supports: Claude, Gemini, Gemma, Qwen
"""

import os
import sys
import json
import time
import csv
import base64
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

# API Keys (must be set via environment variables)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ACADEMICCLOUD_API_KEY = os.getenv("ACADEMICCLOUD_API_KEY")
ACADEMICCLOUD_BASE_URL = "https://chat-ai.academiccloud.de/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model configurations
MODELS = {
    "claude": {
        "model_id": "claude-sonnet-4-5-20250929",
        "api": "anthropic",
        "max_tokens": 2048,
    },
    "gemini": {
        "model_id": "google/gemini-3-pro-preview",
        "api": "openrouter",
        "max_tokens": 8192,  # Higher limit to accommodate reasoning tokens
    },
    "gemma": {
        "model_id": "gemma-3-27b-it",
        "api": "academiccloud",
        "max_tokens": 2048,
    },
    "qwen": {
        "model_id": "qwen2.5-vl-72b-instruct",
        "api": "academiccloud",
        "max_tokens": 2048,
    }
}

# Rate limiting settings
DEFAULT_DELAY = 5
MIN_DELAY = 3
MAX_DELAY = 20

# Default paths (relative to repository root)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SEGMENTS_INDEX = REPO_ROOT / "data/02_results/manuscripts_segments_index.csv"
CROPS_DIR = REPO_ROOT / "data/02_results/crops"
OUTPUT_DIR = REPO_ROOT / "data/02_results/diagram_evaluations"

# ============================================================================
# PROMPTS
# ============================================================================

PROMPTS = {
    "morphological": """OUTPUT FORMAT: JSON only, no explanation.

Count visual elements in this diagram:
1. Cuts (closed curves): How many?
2. Lines (heavy lines): How many? Do any branch?
3. Spots (text labels): How many? What text?

JSON:
{"cuts":{"count":N,"nested":true/false},"lines":{"count":N,"branching":true/false},"spots":{"count":N,"labels":["..."]}}""",
    "indexical": "Is there a relationship between the elements present in the image? Which elements are connected to each other?",
    "symbolic": "In Peirce's diagrammatic logic, a closed curve called a cut represents logical negation. Elements inside the same region are interpreted conjunctively (i.e., asserted together). Elements placed directly on the background (the Sheet of Assertion) are considered true. A cut around propositions denies them. Nested cuts represent nested negation. Lines may indicate identity or existential quantification. Based on these principles, interpret the diagram and translate its meaning into a logical statement. If this is not possible, provide a clear explanation in natural language.",
    "description": "Describe this diagram in detail, including its structure, content, and any visible text or labels.",
    "classification": "What type of diagram is this? (e.g., graph, chart, geometric figure, logical diagram, tree diagram, etc.)",
    "transcription": "Transcribe any text, symbols, or mathematical notation visible in this diagram.",
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_vlm_output(text: str) -> str:
    """Remove common preambles and postambles from VLM output"""
    if text is None:
        return ""

    preambles = [
        "Okay, here's",
        "Here's",
        "Here is",
        "The answer is:",
        "Sure,",
    ]

    for preamble in preambles:
        if text.strip().lower().startswith(preamble.lower()):
            # Find the end of the preamble sentence
            if ":" in text[:100]:
                text = text.split(":", 1)[1].strip()
            break

    return text.strip()

def load_diagram_segments(segments_csv: Path, limit: Optional[int] = None, page_filter: Optional[str] = None) -> List[Dict]:
    """Load diagram segments from CSV index"""
    diagrams = []

    with open(segments_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only process diagrams (class_id = 0), skip text blocks
            if row['segment_class'] == 'diagram':
                # Apply page filter if specified
                page_stem = row['page_filename'].replace('.jpg', '')
                if page_filter and page_stem != page_filter:
                    continue

                # Construct crop path based on actual directory structure
                class_id = row['segment_class_id']
                segment_idx = row['segment_index']

                crop_path = CROPS_DIR / 'cropped' / page_stem / f"{page_stem}_cls{class_id}_{segment_idx}.jpg"

                # Only add if crop exists
                if crop_path.exists():
                    diagrams.append({
                        'manuscript_id': row['manuscript_id'],
                        'page_filename': row['page_filename'],
                        'segment_index': row['segment_index'],
                        'crop_path': crop_path,
                        'x': row['x'],
                        'y': row['y'],
                        'width': row['width'],
                        'height': row['height'],
                        'canvas_uri': row['canvas_uri'],
                        'category_level_1': row['category_level_1'],
                        'category_level_2': row['category_level_2'],
                    })

                    if limit and len(diagrams) >= limit:
                        break

    return diagrams

# ============================================================================
# MODEL-SPECIFIC EVALUATION FUNCTIONS
# ============================================================================

def evaluate_with_claude(client, image_path: Path, prompt: str, model_config: Dict) -> Dict:
    """Evaluate diagram using Claude"""
    try:
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        ext = image_path.suffix.lower()
        media_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'

        message = client.messages.create(
            model=model_config['model_id'],
            max_tokens=model_config['max_tokens'],
            temperature=0,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt}
                ],
            }],
        )

        response_text = message.content[0].text
        response_text = clean_vlm_output(response_text)

        return {
            "success": True,
            "response": response_text,
            "model": model_config['model_id'],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model_config['model_id'],
            "timestamp": datetime.now().isoformat(),
        }

def evaluate_with_gemini(client, image_path: Path, prompt: str, model_config: Dict) -> Dict:
    """Evaluate diagram using Gemini REST API"""
    try:
        import requests

        # Read and encode image
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        image_data = base64.standard_b64encode(image_bytes).decode("utf-8")

        ext = image_path.suffix.lower()
        mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'

        # Construct request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_config['model_id']}:generateContent"

        headers = {
            "x-goog-api-key": GOOGLE_API_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": model_config['max_tokens']
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            error_detail = response.text
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {error_detail}",
                "model": model_config['model_id'],
                "timestamp": datetime.now().isoformat(),
            }

        result = response.json()

        # Extract text from response
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                response_text = candidate['content']['parts'][0].get('text', '')
                response_text = clean_vlm_output(response_text)

                return {
                    "success": True,
                    "response": response_text,
                    "model": model_config['model_id'],
                    "timestamp": datetime.now().isoformat(),
                }

        return {
            "success": False,
            "error": f"No text in response: {result}",
            "model": model_config['model_id'],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model_config['model_id'],
            "timestamp": datetime.now().isoformat(),
        }

def evaluate_with_ollama(image_path: Path, prompt: str, model_config: Dict) -> Dict:
    """Evaluate diagram using Ollama (Gemma/Qwen)"""
    try:
        import requests

        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_config['model_id'],
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": model_config['max_tokens'],
                }
            },
            timeout=120
        )

        response.raise_for_status()
        result = response.json()
        response_text = result.get('response', '')
        response_text = clean_vlm_output(response_text)

        return {
            "success": True,
            "response": response_text,
            "model": model_config['model_id'],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model_config['model_id'],
            "timestamp": datetime.now().isoformat(),
        }

def evaluate_with_openrouter(image_path: Path, prompt: str, model_config: Dict) -> Dict:
    """Evaluate diagram using OpenRouter API"""
    try:
        from openai import OpenAI

        # Initialize client with OpenRouter
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL
        )

        # Encode image
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        # Determine media type
        ext = image_path.suffix.lower()
        media_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'

        # Create message with image
        response = client.chat.completions.create(
            model=model_config['model_id'],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=model_config['max_tokens'],
            temperature=0
        )

        response_text = response.choices[0].message.content
        response_text = clean_vlm_output(response_text)

        # Extract metadata for debugging empty responses
        finish_reason = response.choices[0].finish_reason if response.choices else None

        # Debug: print full response for empty responses
        if not response_text or response_text.strip() == "":
            print(f"    ⚠️  Empty response detected!")
            print(f"    finish_reason: {finish_reason}")
            print(f"    Full response object: {response}")

        return {
            "success": True,
            "response": response_text,
            "finish_reason": finish_reason,
            "model": model_config['model_id'],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model_config['model_id'],
            "timestamp": datetime.now().isoformat(),
        }

def evaluate_with_academiccloud(image_path: Path, prompt: str, model_config: Dict) -> Dict:
    """Evaluate diagram using AcademicCloud OpenAI-compatible API"""
    try:
        from openai import OpenAI

        # Initialize client with custom base URL
        client = OpenAI(
            api_key=ACADEMICCLOUD_API_KEY,
            base_url=ACADEMICCLOUD_BASE_URL
        )

        # Encode image
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        # Determine media type
        ext = image_path.suffix.lower()
        media_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'

        # Create message with image
        response = client.chat.completions.create(
            model=model_config['model_id'],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=model_config['max_tokens'],
            temperature=0
        )

        response_text = response.choices[0].message.content
        response_text = clean_vlm_output(response_text)

        return {
            "success": True,
            "response": response_text,
            "model": model_config['model_id'],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model_config['model_id'],
            "timestamp": datetime.now().isoformat(),
        }

# ============================================================================
# MAIN EVALUATION FUNCTION
# ============================================================================

def evaluate_diagram(client, image_path: Path, prompt: str, model_name: str) -> Dict:
    """Evaluate a single diagram with the specified model"""
    model_config = MODELS[model_name]

    if model_config['api'] == 'anthropic':
        return evaluate_with_claude(client, image_path, prompt, model_config)
    elif model_config['api'] == 'google':
        return evaluate_with_gemini(client, image_path, prompt, model_config)
    elif model_config['api'] == 'ollama':
        return evaluate_with_ollama(image_path, prompt, model_config)
    elif model_config['api'] == 'academiccloud':
        return evaluate_with_academiccloud(image_path, prompt, model_config)
    elif model_config['api'] == 'openrouter':
        return evaluate_with_openrouter(image_path, prompt, model_config)
    else:
        return {
            "success": False,
            "error": f"Unknown API: {model_config['api']}",
            "timestamp": datetime.now().isoformat(),
        }

def process_diagrams(
    model_name: str,
    prompt_key: str,
    custom_prompt: Optional[str] = None,
    limit: Optional[int] = None,
    delay: int = DEFAULT_DELAY,
    page_filter: Optional[str] = None
):
    """Process all diagram segments with specified model and prompt"""

    # Get model config
    if model_name not in MODELS:
        print(f"ERROR: Unknown model '{model_name}'")
        print(f"Available models: {', '.join(MODELS.keys())}")
        return

    model_config = MODELS[model_name]

    # Get prompt
    prompt = custom_prompt if custom_prompt else PROMPTS.get(prompt_key, PROMPTS['morphological'])

    # Initialize API client
    client = None
    if model_config['api'] == 'anthropic':
        if not ANTHROPIC_API_KEY:
            print("ERROR: ANTHROPIC_API_KEY not set!")
            return
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    elif model_config['api'] == 'google':
        if not GOOGLE_API_KEY:
            print("ERROR: GOOGLE_API_KEY not set!")
            return
        from google import genai
        client = genai.Client(api_key=GOOGLE_API_KEY)

    # Load diagram segments
    print("Loading diagram segments from index...")
    diagrams = load_diagram_segments(SEGMENTS_INDEX, limit, page_filter)
    print(f"Found {len(diagrams)} diagram segments to evaluate")
    if page_filter:
        print(f"Filtered to page: {page_filter}")
    print()

    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_clean = model_config['model_id'].replace(':', '_').replace('.', '_').replace('-', '_')
    output_dir = OUTPUT_DIR / model_clean / f"eval_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"DIAGRAM EVALUATION - {model_name.upper()}")
    print("=" * 70)
    print(f"Model: {model_config['model_id']}")
    print(f"Prompt: {prompt[:80]}...")
    print(f"Diagrams: {len(diagrams)}")
    print(f"Output: {output_dir}")
    print(f"Delay: {delay}s")
    print("=" * 70)
    print()

    # Process diagrams
    results = []
    successful = 0
    failed = 0

    for i, diagram in enumerate(diagrams, 1):
        # Create unique ID for this diagram
        diagram_id = f"{diagram['manuscript_id']}_{diagram['page_filename'].replace('.jpg', '')}_{diagram['segment_index']}"

        print(f"[{i}/{len(diagrams)}] {diagram_id}")

        # Check if crop exists
        if not diagram['crop_path'].exists():
            print(f"  ✗ Crop not found: {diagram['crop_path']}")
            failed += 1
            continue

        # Check if already evaluated
        output_file = output_dir / f"{diagram_id}.json"
        if output_file.exists():
            print(f"  ⊘ Already evaluated, skipping")
            successful += 1
            continue

        # Evaluate
        result = evaluate_diagram(client, diagram['crop_path'], prompt, model_name)

        # Save result
        if result['success']:
            # Combine diagram metadata with evaluation result
            full_result = {
                **diagram,
                'crop_path': str(diagram['crop_path']),
                'prompt': prompt,
                'evaluation': result['response'],
                'model': result['model'],
                'timestamp': result['timestamp'],
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(full_result, f, indent=2, ensure_ascii=False)

            print(f"  ✓ Evaluated successfully")
            successful += 1
        else:
            print(f"  ✗ Failed: {result['error']}")
            failed += 1

        results.append({
            'diagram_id': diagram_id,
            **result
        })

        # Rate limiting
        if i < len(diagrams):
            time.sleep(delay)

    # Save summary
    summary = {
        "model": model_config['model_id'],
        "prompt": prompt,
        "total_diagrams": len(diagrams),
        "successful": successful,
        "failed": failed,
        "timestamp": timestamp,
        "results": results
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print(f"Successful: {successful}/{len(diagrams)}")
    print(f"Failed: {failed}/{len(diagrams)}")
    print(f"Output: {output_dir}")
    print(f"Summary: {summary_file.name}")
    print("=" * 70)

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Evaluate diagram segments with vision-language models")
    parser.add_argument('model', choices=list(MODELS.keys()), help='Model to use')
    parser.add_argument('--prompt', choices=list(PROMPTS.keys()), default='morphological', help='Prompt template to use')
    parser.add_argument('--custom-prompt', type=str, help='Custom prompt (overrides --prompt)')
    parser.add_argument('--limit', type=int, help='Limit number of diagrams to process')
    parser.add_argument('--delay', type=int, default=DEFAULT_DELAY, help='Delay between requests (seconds)')
    parser.add_argument('--page', type=str, help='Filter to specific page (e.g., D._Logic__hou02614c00458__seq15)')

    args = parser.parse_args()

    process_diagrams(
        model_name=args.model,
        prompt_key=args.prompt,
        custom_prompt=args.custom_prompt,
        limit=args.limit,
        delay=args.delay,
        page_filter=args.page
    )

if __name__ == "__main__":
    main()
