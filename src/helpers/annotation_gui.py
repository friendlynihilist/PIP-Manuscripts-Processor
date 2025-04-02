import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import pandas as pd

# CONFIG
IMAGE_FOLDER = "manual_annotation"
LABELS_CSV = "manual_annotation_labels.csv"
OUTPUT_CSV = "manual_annotation_corrected.csv"
CATEGORIES = ["text", "diagram", "sketch", "cover", "blank", "other"]

# Load image paths from CSV
df = pd.read_csv(LABELS_CSV)
df["corrected_label"] = ""

# Create output directory
if os.path.exists(OUTPUT_CSV):
    df_existing = pd.read_csv(OUTPUT_CSV)
    df.update(df_existing)

index = 0
while index < len(df) and isinstance(df.loc[index, "corrected_label"], str) and df.loc[index, "corrected_label"].strip() != "":
    index += 1

# GUI
root = tk.Tk()
root.title("Manual Annotation Tool")

image_label = tk.Label(root)
image_label.pack()

label_var = tk.StringVar()
label_menu = tk.OptionMenu(root, label_var, *CATEGORIES)
label_menu.pack()

def save_and_next():
    global index
    label = label_var.get()
    if label:
        df.loc[index, "corrected_label"] = label
        index += 1
        if index >= len(df):
            df.to_csv(OUTPUT_CSV, index=False)
            root.quit()
        else:
            show_image()

def show_image():
    image_path = os.path.join(IMAGE_FOLDER, df.loc[index, "predicted_label"], df.loc[index, "filename"])
    if not os.path.exists(image_path):
        print("Missing image:", image_path)
        return
    img = Image.open(image_path)
    img.thumbnail((500, 700), Image.Resampling.LANCZOS)
    img_tk = ImageTk.PhotoImage(img)
    image_label.configure(image=img_tk)
    image_label.image = img_tk
    root.title(f"{index + 1} / {len(df)} - {df.loc[index, 'filename']}")
    label_var.set("")

btn = tk.Button(root, text="Save & Next", command=save_and_next)
btn.pack()

show_image()
root.mainloop()
