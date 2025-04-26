import pandas as pd
import random
import os

# --- CONFIGURATION ---
input_csv = "supervised_annotations.csv"
train_csv = "train.csv"
test_csv = "test.csv"
test_ratio = 0.2  # 20% test, 80% train
random_seed = 42  # For reproducibility

# --- Load Data ---
df = pd.read_csv(input_csv)

# --- Filter only meaningful classes ---
df = df[df['Label'].isin(["diagram_mixed", "text", "cover"])]

print(f"📊 Dataset size after filtering: {len(df)} samples")

# --- Shuffle the data ---
df = df.sample(frac=1, random_state=random_seed).reset_index(drop=True)

# --- Split train/test ---
split_idx = int(len(df) * (1 - test_ratio))
train_df = df.iloc[:split_idx]
test_df = df.iloc[split_idx:]

# --- Save ---
train_df.to_csv(train_csv, index=False)
test_df.to_csv(test_csv, index=False)

print(f"✅ Saved {len(train_df)} training samples to {train_csv}")
print(f"✅ Saved {len(test_df)} testing samples to {test_csv}")
