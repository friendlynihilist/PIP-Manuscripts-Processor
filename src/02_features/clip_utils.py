"""
Shared CLIP utilities for PIP Manuscripts Processor.

This module ensures consistency across all CLIP-based feature extraction scripts
by providing a single source of truth for model configuration.

IMPORTANT: All CLIP extraction scripts should use this module to load the model
to ensure embedding compatibility across the pipeline.
"""

import torch
import open_clip
from PIL import Image


# === CLIP MODEL CONFIGURATION ===
# Use ViT-B-32-quickgelu consistently across all scripts
CLIP_MODEL_NAME = "ViT-B-32-quickgelu"
CLIP_PRETRAINED = "openai"


def get_clip_model(device=None):
    """
    Load the standard CLIP model used throughout the pipeline.

    Args:
        device: torch device (cuda/cpu). If None, automatically selects.

    Returns:
        tuple: (model, transform, preprocess) from open_clip

    Note:
        This ensures all embeddings are extracted with the same model variant,
        making them directly comparable for classification and analysis.
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    model, _, preprocess = open_clip.create_model_and_transforms(
        CLIP_MODEL_NAME,
        pretrained=CLIP_PRETRAINED
    )
    model.eval().to(device)

    return model, device, preprocess


def extract_clip_embedding(image_path, model, preprocess, device):
    """
    Extract CLIP embedding from a single image.

    Args:
        image_path: Path to image file
        model: CLIP model from get_clip_model()
        preprocess: Preprocessing transform from get_clip_model()
        device: torch device

    Returns:
        numpy.ndarray: Flattened CLIP embedding vector

    Raises:
        Exception: If image cannot be loaded or processed
    """
    img = Image.open(image_path).convert("RGB")
    img_tensor = preprocess(img).unsqueeze(0).to(device)

    with torch.no_grad():
        embedding = model.encode_image(img_tensor).cpu().numpy().flatten()

    return embedding


def load_image_and_preprocess(image_path):
    """
    Load and convert image to RGB.

    Args:
        image_path: Path to image file

    Returns:
        PIL.Image: RGB image or None if loading fails
    """
    try:
        img = Image.open(image_path).convert("RGB")
        return img
    except Exception as e:
        print(f"❌ Failed to load {image_path}: {e}")
        return None


# === CONFIGURATION INFO ===
def get_model_info():
    """Return information about the CLIP model configuration."""
    return {
        "model_name": CLIP_MODEL_NAME,
        "pretrained": CLIP_PRETRAINED,
        "embedding_dim": 512,  # ViT-B-32 output dimension
        "description": "OpenAI ViT-B-32 with QuickGELU activation"
    }


if __name__ == "__main__":
    # Print model configuration
    info = get_model_info()
    print("CLIP Model Configuration:")
    print(f"  Model: {info['model_name']}")
    print(f"  Pretrained: {info['pretrained']}")
    print(f"  Embedding dimension: {info['embedding_dim']}")
    print(f"  Description: {info['description']}")

    # Test model loading
    print("\nTesting model loading...")
    model, device, preprocess = get_clip_model()
    print(f"✅ Model loaded successfully on device: {device}")
