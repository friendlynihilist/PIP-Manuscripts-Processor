import os
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm
from skimage.feature import hog
from sklearn.preprocessing import LabelEncoder
import torch
import torchvision.transforms as T
from torchvision.models import resnet50
import open_clip
from clip_utils import get_clip_model

# === CONFIG ===
train_csv = "train.csv"
test_csv = "test.csv"
output_dir = "preprocessed_data"
os.makedirs(output_dir, exist_ok=True)

image_size = (224, 224)  # For CNN and CLIP

# === DEVICE ===
device = "cuda" if torch.cuda.is_available() else "cpu"

# === CNN MODEL ===
cnn_model = resnet50(pretrained=True)
cnn_model.fc = torch.nn.Identity()  # Remove final classification layer
cnn_model.eval().to(device)

cnn_transform = T.Compose([
    T.Resize(image_size),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# === CLIP MODEL ===
# Use shared CLIP utilities to ensure consistency across pipeline
clip_model, device, clip_preprocess = get_clip_model(device)

# === HOG CONFIG ===
hog_params = {
    'pixels_per_cell': (16, 16),
    'cells_per_block': (2, 2),
    'orientations': 9,
    'feature_vector': True
}

# === FUNCTIONS ===
def load_and_preprocess(img_path):
    try:
        img = Image.open(img_path).convert("RGB")
        return img
    except:
        return None

def extract_features(row):
    img_path = row["Path"]
    label = row["Label"]
    img = load_and_preprocess(img_path)
    if img is None:
        return None

    # HOG
    gray_img = img.convert("L").resize(image_size)
    hog_feat = hog(np.array(gray_img), **hog_params)

    # CNN
    cnn_input = cnn_transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        cnn_feat = cnn_model(cnn_input).cpu().numpy().flatten()

    # CLIP
    clip_input = clip_preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        clip_feat = clip_model.encode_image(clip_input).cpu().numpy().flatten()

    return hog_feat, cnn_feat, clip_feat, label

def process_dataset(df, prefix):
    hog_feats, cnn_feats, clip_feats, labels = [], [], [], []

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Extracting {prefix}"):
        result = extract_features(row)
        if result:
            h, c, cl, lbl = result
            hog_feats.append(h)
            cnn_feats.append(c)
            clip_feats.append(cl)
            labels.append(lbl)

    return np.array(hog_feats), np.array(cnn_feats), np.array(clip_feats), labels

# === LOAD DATA ===
train_df = pd.read_csv(train_csv)
test_df = pd.read_csv(test_csv)

# === PROCESS ===
hog_train, cnn_train, clip_train, y_train_raw = process_dataset(train_df, "Train")
hog_test, cnn_test, clip_test, y_test_raw = process_dataset(test_df, "Test")

# === ENCODE LABELS ===
le = LabelEncoder()
y_train = le.fit_transform(y_train_raw)
y_test = le.transform(y_test_raw)

# === SAVE ===
np.save(os.path.join(output_dir, "X_train_hog.npy"), hog_train)
np.save(os.path.join(output_dir, "X_test_hog.npy"), hog_test)

np.save(os.path.join(output_dir, "X_train_cnn.npy"), cnn_train)
np.save(os.path.join(output_dir, "X_test_cnn.npy"), cnn_test)

np.save(os.path.join(output_dir, "X_train_clip.npy"), clip_train)
np.save(os.path.join(output_dir, "X_test_clip.npy"), clip_test)

np.save(os.path.join(output_dir, "y_train.npy"), y_train)
np.save(os.path.join(output_dir, "y_test.npy"), y_test)

with open(os.path.join(output_dir, "label_encoder.pkl"), "wb") as f:
    import pickle
    pickle.dump(le, f)

print("✅ All features extracted and saved.")