import os

# --- CONFIGURATION ---
root_dir = "Manuscripts"
image_extensions = (".jpg", ".jpeg")
total_count = 0

# --- Traverse folders ---
for dirpath, dirnames, filenames in os.walk(root_dir):
    count = sum(1 for file in filenames if file.lower().endswith(image_extensions))
    total_count += count

print(f"📷 Total .jpg/.jpeg images in '{root_dir}': {total_count}")
