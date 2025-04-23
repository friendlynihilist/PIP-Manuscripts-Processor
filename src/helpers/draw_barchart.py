import json
import pandas as pd
import matplotlib.pyplot as plt
import os

# === Load JSON ===
json_file_path = "collection_metadata.json"
output_dir = "./"  # Change if needed

with open(json_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# === Convert to DataFrame ===
df = pd.DataFrame(data)

# === Filter for manuscripts only ===
df_manuscripts = df[df["Category Level 1"].str.strip() == "I. Manuscripts"]

# === Remove empty Category Level 2 ===
df_manuscripts = df_manuscripts[df_manuscripts["Category Level 2"].notnull()]
df_manuscripts = df_manuscripts[df_manuscripts["Category Level 2"].str.strip() != ""]

# === Count total items per category ===
total_counts = df_manuscripts["Category Level 2"].value_counts().sort_index()

# === Count digitized items per category ===
df_digital = df_manuscripts[df_manuscripts["Digital Link"].notnull()]
df_digital = df_digital[df_digital["Digital Link"].str.strip() != ""]
digital_counts = df_digital["Category Level 2"].value_counts().sort_index()

# === Combine counts ===
combined_counts = pd.DataFrame({
    "Total Items": total_counts,
    "Digitized Items": digital_counts
}).fillna(0).astype(int)

# === Export CSV ===
csv_output_path = os.path.join(output_dir, "category_distribution.csv")
combined_counts.to_csv(csv_output_path)
print(f"✅ CSV saved to {csv_output_path}")

# === Plotting ===
fig, ax = plt.subplots(figsize=(12, 6))
bar_width = 0.4
x = range(len(combined_counts.index))

# Bars
ax.bar(x, combined_counts["Total Items"], width=bar_width, label="Total Items")
ax.bar([i + bar_width for i in x], combined_counts["Digitized Items"], width=bar_width, label="Digitized Items", color="skyblue")

# Labels
for i in x:
    ax.text(i, combined_counts["Total Items"].iloc[i] + 1, str(combined_counts["Total Items"].iloc[i]), ha='center', fontsize=8)
    ax.text(i + bar_width, combined_counts["Digitized Items"].iloc[i] + 1, str(combined_counts["Digitized Items"].iloc[i]), ha='center', fontsize=8, color='blue')

# Axis setup
ax.set_xticks([i + bar_width / 2 for i in x])
ax.set_xticklabels(combined_counts.index, rotation=45, ha="right")
ax.set_title("Distribution of Manuscripts and Digitized Items by Category (Level 2)")
ax.set_ylabel("Number of Items")
ax.set_xlabel("Category")
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

# === Save image ===
image_output_path = os.path.join(output_dir, "category_distribution.png")
plt.savefig(image_output_path)
print(f"🖼️ Image saved to {image_output_path}")

plt.show()
