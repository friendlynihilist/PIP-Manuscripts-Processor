import cv2
import pytesseract
import os
import numpy as np
import pandas as pd

IMAGE_FOLDER = "Manuscripts/A. Mathematics/Peirce_ Charles S. (Charles Sanders)_ 1839-1914. An Attempt to state systematically the Doctrine of "
OUTPUT_CSV = "page_analysis_results.csv"

pytesseract.pytesseract.tesseract_cmd = r"/opt/homebrew/bin/tesseract"

def detect_diagram(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    # Apply Canny Edge Detection to detect sharp edges (diagrams usually have strong edges)
    edges = cv2.Canny(image, 50, 150)

    # Count the number of edges
    edge_density = np.sum(edges) / (image.shape[0] * image.shape[1])

    # OCR: Extract text from the image
    text = pytesseract.image_to_string(image)
    text_length = len(text.strip())

    # Classify based on edge density and text length
    if edge_density > 0.01 and text_length < 50:  
        return "Diagram"
    elif text_length > 200:  
        return "Text Page"
    else:
        return "Uncertain"

# Process all images in the folder
results = []
for filename in os.listdir(IMAGE_FOLDER):
    if filename.endswith((".jpg", ".png", ".tif")):
        image_path = os.path.join(IMAGE_FOLDER, filename)
        classification = detect_diagram(image_path)
        results.append({"Image": filename, "Classification": classification})

# Save results to CSV
df_results = pd.DataFrame(results)
df_results.to_csv(OUTPUT_CSV, index=False)

print(f"Analysis complete. Results saved in {OUTPUT_CSV}")
