import os
import re
import json
import requests

# ---------- CONFIG ----------
METADATA_JSON = "metadata.json"
UPDATED_METADATA_JSON = "metadata_updated.json"
BASE_OUTPUT = "Manuscripts"
LIMIT = 1000

def sanitize_filename(name, max_length=100):
    """Sanitize a string for use as a folder/file name."""
    sanitized = "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name).strip()
    return sanitized[:max_length]

def resolve_redirect(url):
    """Follow redirects and return the final URL."""
    try:
        response = requests.get(url, allow_redirects=True, timeout=10)
        print(f"Resolved URL: {url} -> {response.url}")
        return response.url
    except Exception as e:
        print(f"Error resolving URL {url}: {e}")
        return None

def clean_manifest_url(url):
    """
    Convert a viewer URL into a direct manifest URL.
    If the URL contains '/view/', remove that segment and any trailing query parameters or fragments.
    For example:
      Input:  https://iiif.lib.harvard.edu/manifests/view/ids:52083131?buttons=y
      Output: https://iiif.lib.harvard.edu/manifests/ids:52083131
    """
    if "/view/" in url:
        base, _, tail = url.partition("/view/")
        tail = tail.split("?")[0].split("$")[0]
        manifest_url = base + "/" + tail
        print(f"Cleaned manifest URL: {manifest_url}")
        return manifest_url
    return url

def download_manifest(manifest_uri):
    """Fetch and return the manifest JSON from the manifest URI."""
    try:
        response = requests.get(manifest_uri, timeout=10)
        response.raise_for_status()
        print(f"Downloaded manifest from {manifest_uri}")
        return response.json()
    except Exception as e:
        print(f"Error downloading manifest from {manifest_uri}: {e}")
        return None

def download_image(url, path):
    """Download an image from a URL and save it to the given path."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded image to {path}")
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")

def process_item(item):
    """
    Given an item from metadata.json, fetch its manifest, update the metadata with the manifest label (if not yet present),
    create folders (using the fetched manifest label), download the manifest JSON and images, and save canvas metadata in a single JSON file.
    """
    manifest_uri = item.get("Manifest URI", "")
    if not manifest_uri:
        print("No Manifest URI found; skipping item.")
        return
    
    manifest_json = download_manifest(manifest_uri)
    if not manifest_json:
        print(f"Skipping item with Manifest URI {manifest_uri} due to download error.")
        return
    
    manifest_label = manifest_json.get("label", "Untitled Manifest")
    
    if "label" not in item or not item["label"]:
        item["label"] = manifest_label
        print(f"Updated metadata with label: {manifest_label}")
    
    folder_name = sanitize_filename(manifest_label)
    
    category = item.get("Category", "Uncategorized")
    category_folder = os.path.join(BASE_OUTPUT, sanitize_filename(category))
    os.makedirs(category_folder, exist_ok=True)
    
    item_folder = os.path.join(category_folder, folder_name)
    os.makedirs(item_folder, exist_ok=True)
    
    manifest_path = os.path.join(item_folder, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_json, f, indent=4, ensure_ascii=False)
    print(f"Saved manifest to {manifest_path}")
    
    m = re.search(r"\d+", manifest_uri)
    manifest_digits = m.group() if m else "unknown"
    
    sequences = manifest_json.get("sequences", [])
    if not sequences:
        print("No sequences found in manifest.")
        return
    canvases = sequences[0].get("canvases", [])
    
    canvas_metadata_list = []
    for idx, canvas in enumerate(canvases):
        canvas_label = canvas.get("label", "Unknown Canvas")
        canvas_id = canvas.get("@id", "")
        page_height = canvas.get("height", "")
        page_width = canvas.get("width", "")
        image_url = ""
        images = canvas.get("images", [])
        if images:
            image_url = images[0].get("resource", {}).get("@id", "")
        thumbnail_url = ""
        thumb = canvas.get("thumbnail", {})
        if isinstance(thumb, dict):
            thumbnail_url = thumb.get("@id", "")
        
        image_filename = f"seq{idx+1}.jpg"
        image_path = os.path.join(item_folder, image_filename)
        if image_url:
            download_image(image_url, image_path)
        
        canvas_metadata = {
            "Manifest Title": manifest_label,
            "Manifest ID": manifest_uri,
            "Canvas Label": canvas_label,
            "Canvas ID": canvas_id,
            "Image Filename": image_filename,
            "Image URL": image_url,
            "Thumbnail URL": thumbnail_url,
            "Page Height": page_height,
            "Page Width": page_width
        }
        canvas_metadata_list.append(canvas_metadata)
    
    canvas_json_filename = f"{manifest_digits}.json"
    canvas_json_path = os.path.join(item_folder, canvas_json_filename)
    with open(canvas_json_path, "w", encoding="utf-8") as f:
        json.dump(canvas_metadata_list, f, indent=4, ensure_ascii=False)
    print(f"Saved canvas metadata to {canvas_json_path}")

def main():
    with open(METADATA_JSON, "r", encoding="utf-8") as f:
        metadata_list = json.load(f)
    
    processed_count = 0
    for item in metadata_list:
        if processed_count >= LIMIT:
            break
        process_item(item)
        processed_count += 1
    
    with open(UPDATED_METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, indent=4, ensure_ascii=False)
    print(f"Updated metadata saved to {UPDATED_METADATA_JSON}")

if __name__ == "__main__":
    main()
