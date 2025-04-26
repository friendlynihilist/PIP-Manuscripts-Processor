import os
import json
import csv
import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk
import re
import random

# --- CONFIGURATION ---
metadata_path = "collection_metadata.json"
filtered_csv = "filtered_candidates.csv"
output_csv = "supervised_annotations.csv"

label_map = {
    "1": "diagram",
    "2": "text",
    "3": "mixed",
    "4": "sketch",
    "5": "cover"
}

# --- Sanitize filenames ---
def sanitize(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).strip()

# --- Load existing annotations and blanks ---
excluded_blanks = set()
label_counts = {label: 0 for label in label_map.values()}
annotated_paths = set()

if os.path.exists(output_csv):
    with open(output_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            path = row["Image Path"]
            lbl = row.get("Label", "").strip().lower()
            if lbl == "blank":
                excluded_blanks.add(path)
            elif lbl in label_counts:
                annotated_paths.add(path)
                label_counts[lbl] += 1

# --- Load filtered candidates ---
images_to_annotate = []
if os.path.exists(filtered_csv):
    with open(filtered_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            path = row["Image Path"]
            if path in excluded_blanks or path in annotated_paths:
                continue
            images_to_annotate.append((
                row["ID"],
                path,
                row["Canvas Label"],
                row["Filename"]
            ))

random.shuffle(images_to_annotate)

# --- Annotator UI ---
class ImageAnnotator:
    def __init__(self, master, images):
        self.master = master
        self.images = images
        self.index = 0

        self.label = Label(master)
        self.label.pack()

        self.legend = Label(master, text=self.get_legend_text(), font=("Helvetica", 10))
        self.legend.pack(pady=4)

        self.count_display = Label(master, text=self.get_count_text(), font=("Helvetica", 10, "bold"))
        self.count_display.pack(pady=4)

        self.master.bind("<Key>", self.key_pressed)
        self.show_image()

    def get_legend_text(self):
        legend = " | ".join(f"{k} - {v}" for k, v in label_map.items())
        return legend + " | s - skip"

    def get_count_text(self):
        return " | ".join(f"{label}: {count}" for label, count in label_counts.items())

    def show_image(self):
        if self.index >= len(self.images):
            print("✅ All images annotated.")
            self.master.quit()
            return

        item_id, img_path, canvas_label, filename = self.images[self.index]
        img = Image.open(img_path)
        img = img.resize((min(500, img.width), int(img.height * (min(500, img.width) / img.width))), Image.Resampling.LANCZOS)
        self.tkimage = ImageTk.PhotoImage(img)
        self.label.config(image=self.tkimage)
        self.master.title(f"{self.index + 1}/{len(self.images)}: {img_path} | Canvas: {canvas_label}")

    def key_pressed(self, event):
        key = event.char.lower()
        if key in label_map:
            label = label_map[key]
            self.save_annotation(label)
        elif key == "s":
            print("⏭️ Skipped.")
            self.index += 1
            self.show_image()
        elif event.keysym == "Escape":
            self.master.quit()

    def save_annotation(self, label):
        item_id, img_path, canvas_label, filename = self.images[self.index]
        with open(output_csv, "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["ID", "Image Path", "Canvas Label", "Filename", "Label"])
            writer.writerow([item_id, img_path, canvas_label, filename, label])

        print(f"✅ Labeled: {img_path} as {label}")
        label_counts[label] += 1
        self.count_display.config(text=self.get_count_text())
        self.index += 1
        self.show_image()

# --- Run GUI ---
if images_to_annotate:
    root = tk.Tk()
    app = ImageAnnotator(root, images_to_annotate)
    root.mainloop()
else:
    print("✅ No new images to annotate.")
