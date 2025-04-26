import csv
from collections import Counter

# --- CONFIGURATION ---
input_csv = "supervised_annotations_relabelled.csv"  # or your new corrected CSV

# --- COUNTING ---
label_counter = Counter()

with open(input_csv, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        label = row.get("Annotated Label", "").strip().lower()
        if label:
            label_counter[label] += 1

# --- OUTPUT ---
print("\n📊 Label Counts:")
for label, count in label_counter.most_common():
    print(f" - {label}: {count}")

print("\n✅ Done.")
