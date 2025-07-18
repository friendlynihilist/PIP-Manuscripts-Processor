import clip
import torch
from PIL import Image

# Carica il modello CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Carica immagine e caption
image = preprocess(Image.open("imagetest.jpg")).unsqueeze(0).to(device)

caption_text = (
    "The image contains three words ('man', 'wounded', 'disgraced'), "
    "a horizontal line extending from 'man', a branching arc connecting "
    "to 'wounded' and 'disgraced', and an oval enclosing the two latter words. "
    "These elements form a conceptual diagram linking 'man' to two conditions."
)

caption = clip.tokenize([caption_text]).to(device)

# Calcola le embedding
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(caption)

# Normalizza
image_features /= image_features.norm(dim=-1, keepdim=True)
text_features /= text_features.norm(dim=-1, keepdim=True)

# Calcola il CLIPScore (cosine similarity * 100)
similarity = (image_features @ text_features.T).item()
clipscore = similarity * 100

print(f"CLIPScore: {clipscore:.2f}")