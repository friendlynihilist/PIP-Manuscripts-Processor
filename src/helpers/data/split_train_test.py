import pandas as pd
import random
import os

# --- CONFIG ---
input_csv = "supervised_annotations.csv"
train_csv = "train.csv"
test_csv = "test.csv"
test_ratio = 0.2  # 20% test, 80% train
random_seed = 42  # For reproducibility

# --- Load Data ---
df = pd.read_csv(input_csv)

# --- Filter ---
df = df[df['Label'].isin(["diagram_mixed", "text", "cover"])]
df = df.sample(frac=1, random_state=random_seed).reset_index(drop=True)

# --- Split ---
split_idx = int(len(df) * (1 - test_ratio))
train_df = df.iloc[:split_idx]
test_df = df.iloc[split_idx:]

train_df.to_csv(train_csv, index=False)
test_df.to_csv(test_csv, index=False)
