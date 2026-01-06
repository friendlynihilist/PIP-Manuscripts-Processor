#!/usr/bin/env python3
"""
Unified Manuscript Transcription Script
Supports: Claude, Gemini, Gemma, Qwen
"""

import os
import sys
import json
import time
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
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Base URLs
ACADEMICCLOUD_BASE_URL = "https://chat-ai.academiccloud.de/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model configurations
MODELS = {
    "claude": {
        "model_id": "claude-sonnet-4-5-20250929",
        "api": "anthropic",
        "display_name": "Claude Sonnet 4.5",
    },
    "gemini": {
        "model_id": "gemini-3-pro-preview",
        "api": "google",
        "display_name": "Google Gemini 3 Pro Preview",
    },
    "gemma": {
        "model_id": "gemma-3-27b-it",
        "api": "academiccloud",
        "display_name": "Gemma 3 27B IT",
    },
    "qwen": {
        "model_id": "qwen2.5-vl-72b-instruct",
        "api": "academiccloud",
        "display_name": "Qwen 2.5 VL 72B Instruct",
    }
}

# Rate limiting settings
INITIAL_DELAY = 5
MIN_DELAY = 3
MAX_DELAY = 20

# Default paths (relative to repository root)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CORPUS_DIR = REPO_ROOT / "data/00_raw/manuscripts/Manuscripts"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data/02_results/transcriptions"
BLANK_PAGES_FILE = REPO_ROOT / "data/00_raw/metadata/hou02614c00458_blank_pages.json"

# Transcription prompt
TRANSCRIPTION_PROMPT = """Your task is to accurately transcribe this handwritten historical document. Work character by character, word by word, line by line, transcribing the text exactly as it appears on the page. Retain all spelling errors, grammar, syntax, capitalization, and punctuation as well as line breaks. Transcribe all text including headers, footers, and marginalia. If insertions or marginalia are present, insert them where indicated by the author. When you encounter visual elements such as diagrams, figures, or illustrations, insert the placeholder [DIAGRAM:n] at their location in the text, where n indicates the sequential number (1, 2, 3, etc.). Use [unclear] for illegible text. In your final response write only your transcription."""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_vlm_output(text: str) -> str:
    """Remove common preambles and postambles from VLM output"""
    if text is None:
        return ""

    preambles = [
        "Okay, here's the transcribed text:",
        "Here's the transcription:",
        "Here is the transcribed text:",
        "The transcribed text is:",
        "Transcription:",
        "Here you go:",
        "Sure, here's the transcription:",
    ]

    for preamble in preambles:
        if text.lower().startswith(preamble.lower()):
            text = text[len(preamble):].strip()
            break

    postambles = [
        "Let me know if you need any clarification.",
        "Is there anything else you need?",
        "Would you like me to help with anything else?",
    ]

    for postamble in postambles:
        if text.lower().endswith(postamble.lower()):
            text = text[:-len(postamble)].strip()
            break

    return text

def load_blank_pages(manuscript_id: str) -> set:
    """Load blank page sequences for a manuscript"""
    if not BLANK_PAGES_FILE.exists():
        return set()

    try:
        with open(BLANK_PAGES_FILE) as f:
            data = json.load(f)
            if data.get('manuscript_id') == manuscript_id:
                return set(data.get('blank_sequences', []))
    except Exception as e:
        print(f"Warning: Could not load blank pages file: {e}")

    return set()

def find_manuscript_folder(corpus_dir: Path, manuscript_id: str) -> Optional[Path]:
    """Find manuscript folder in corpus"""
    manuscript_folders = list(corpus_dir.glob(f"**/{manuscript_id}"))
    if not manuscript_folders:
        return None
    return manuscript_folders[0]

def get_images_from_manuscript(manuscript_folder: Path, skip_blank: bool = False,
                               manuscript_id: str = None) -> List[Path]:
    """Get all images from manuscript folder, optionally skipping blank pages"""
    images = []

    # Load blank pages if needed
    blank_pages = set()
    if skip_blank and manuscript_id:
        blank_pages = load_blank_pages(manuscript_id)

    # Collect all image files
    for img in sorted(manuscript_folder.glob("seq*.jpg")):
        images.append(img)
    for img in sorted(manuscript_folder.glob("seq*.png")):
        jpg_version = manuscript_folder / f"{img.stem}.jpg"
        if not jpg_version.exists():
            images.append(img)

    # Filter blank pages if requested
    if skip_blank and blank_pages:
        import re
        filtered = []
        for img in images:
            # Extract sequence number from filename (e.g., seq123.jpg -> 123)
            match = re.search(r'seq(\d+)', img.name)
            if match:
                seq_num = int(match.group(1))
                if seq_num not in blank_pages:
                    filtered.append(img)
        return sorted(filtered, key=lambda x: x.name)

    return sorted(images, key=lambda x: x.name)

# ============================================================================
# MODEL-SPECIFIC TRANSCRIPTION FUNCTIONS
# ============================================================================

def transcribe_with_claude(image_path: Path) -> str:
    """Transcribe using Claude/Anthropic API"""
    from anthropic import Anthropic

    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    # Determine media type
    ext = image_path.suffix.lower()
    media_type = "image/jpeg" if ext in ['.jpg', '.jpeg'] else "image/png"

    # Make API call
    response = client.messages.create(
        model=MODELS["claude"]["model_id"],
        max_tokens=4096,
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
                {
                    "type": "text",
                    "text": TRANSCRIPTION_PROMPT
                }
            ],
        }]
    )

    return response.content[0].text

def transcribe_with_gemini(image_path: Path) -> str:
    """Transcribe using Google Gemini API"""
    from google import genai
    from google.genai import types

    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    client = genai.Client(api_key=GOOGLE_API_KEY)

    # Read image
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Create content parts
    contents = [
        types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg"
        ),
        types.Part.from_text(TRANSCRIPTION_PROMPT)
    ]

    # Make API call
    response = client.models.generate_content(
        model=MODELS["gemini"]["model_id"],
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=8192,
        )
    )

    return response.text

def transcribe_with_openai_compatible(image_path: Path, model_key: str,
                                     base_url: str, api_key: str) -> str:
    """Transcribe using OpenAI-compatible API (for Gemma, Qwen via AcademicCloud)"""
    from openai import OpenAI

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    # Make API call
    response = client.chat.completions.create(
        model=MODELS[model_key]["model_id"],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": TRANSCRIPTION_PROMPT
                    }
                ]
            }
        ],
        max_tokens=4096,
        temperature=0.0,
    )

    return response.choices[0].message.content

def transcribe_image(image_path: Path, model: str) -> str:
    """Dispatch to appropriate transcription function based on model"""
    print(f"  Processing: {image_path.name}")

    try:
        if model == "claude":
            result = transcribe_with_claude(image_path)
        elif model == "gemini":
            result = transcribe_with_gemini(image_path)
        elif model == "gemma":
            if not ACADEMICCLOUD_API_KEY:
                raise ValueError("ACADEMICCLOUD_API_KEY environment variable not set")
            result = transcribe_with_openai_compatible(
                image_path, "gemma", ACADEMICCLOUD_BASE_URL, ACADEMICCLOUD_API_KEY
            )
        elif model == "qwen":
            if not ACADEMICCLOUD_API_KEY:
                raise ValueError("ACADEMICCLOUD_API_KEY environment variable not set")
            result = transcribe_with_openai_compatible(
                image_path, "qwen", ACADEMICCLOUD_BASE_URL, ACADEMICCLOUD_API_KEY
            )
        else:
            raise ValueError(f"Unknown model: {model}")

        return clean_vlm_output(result)

    except Exception as e:
        print(f"  Error: {e}")
        return f"[ERROR: {str(e)}]"

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def transcribe_manuscript(manuscript_id: str, model: str, corpus_dir: Path,
                         output_dir: Path, skip_blank: bool = False,
                         delay: float = INITIAL_DELAY):
    """Transcribe all pages of a manuscript"""

    # Find manuscript folder
    print(f"Looking for manuscript {manuscript_id}...")
    manuscript_folder = find_manuscript_folder(corpus_dir, manuscript_id)

    if not manuscript_folder:
        print(f"Error: Manuscript {manuscript_id} not found in {corpus_dir}")
        return

    print(f"Found: {manuscript_folder}")

    # Get images
    images = get_images_from_manuscript(manuscript_folder, skip_blank, manuscript_id)
    print(f"Found {len(images)} images to process")

    if skip_blank:
        print(f"  (Skipping blank pages)")

    # Create output directory
    model_name = MODELS[model]["display_name"].replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / manuscript_id / model_name / timestamp
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Output: {output_path}")
    print(f"Model: {MODELS[model]['display_name']}")
    print(f"Delay: {delay}s between requests\n")

    # Process each image
    results = []

    for i, image_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}]", end=" ")

        # Transcribe
        transcription = transcribe_image(image_path, model)

        # Store result
        result = {
            "image": image_path.name,
            "sequence": i,
            "transcription": transcription,
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)

        # Save individual result
        result_file = output_path / f"{image_path.stem}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Rate limiting
        if i < len(images):
            time.sleep(delay)

    # Save consolidated results
    manifest = {
        "manuscript_id": manuscript_id,
        "model": MODELS[model]["display_name"],
        "model_id": MODELS[model]["model_id"],
        "total_pages": len(results),
        "timestamp": timestamp,
        "skip_blank": skip_blank,
        "results": results
    }

    manifest_file = output_path / "manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Complete! Results saved to {output_path}")
    print(f"  Total pages processed: {len(results)}")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Transcribe manuscript pages using various VLM models"
    )
    parser.add_argument(
        "model",
        choices=list(MODELS.keys()),
        help="Model to use for transcription"
    )
    parser.add_argument(
        "--manuscript",
        required=True,
        help="Manuscript ID (e.g., hou02614c00458)"
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=DEFAULT_CORPUS_DIR,
        help=f"Path to corpus directory (default: {DEFAULT_CORPUS_DIR})"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Path to output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--skip-blank",
        action="store_true",
        help="Skip blank pages (uses metadata if available)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=INITIAL_DELAY,
        help=f"Delay between API calls in seconds (default: {INITIAL_DELAY})"
    )

    args = parser.parse_args()

    # Validate API keys
    if args.model == "claude" and not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    elif args.model == "gemini" and not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY environment variable not set")
        sys.exit(1)
    elif args.model in ["gemma", "qwen"] and not ACADEMICCLOUD_API_KEY:
        print("Error: ACADEMICCLOUD_API_KEY environment variable not set")
        sys.exit(1)

    # Run transcription
    transcribe_manuscript(
        manuscript_id=args.manuscript,
        model=args.model,
        corpus_dir=args.corpus_dir,
        output_dir=args.output_dir,
        skip_blank=args.skip_blank,
        delay=args.delay
    )

if __name__ == "__main__":
    main()
