import pdfplumber
import re
import json
import requests

# ---------- CONFIGURATION ----------
PDF_FILE = "hou02614.pdf"  # your PDF filename
OUTPUT_JSON = "metadata.json"
START_PAGE = 6
END_PAGE = 309

CATEGORIES = [
    "A. Mathematics",
    "B. Pragmatism",
    "C. Phenomenology",
    "D. Logic",
    "E. Metaphysics",
    "F. Physics",
    "G. Chemistry",
    "H. Astronomy",
    "I. Geodesy and metrology",
    "J. Psychology",
    "K. Linguistics",
    "L. History",
    "M. Sciences of review",
    "N. Practical science",
    "O. Reviews",
    "P. Translations",
    "Q. Miscellanea"
]

# ---------- HELPER FUNCTIONS ----------

def resolve_redirect(url):
    """Follow redirects to get the final URL."""
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
    If the URL contains '/view/', remove that segment and anything after a '$' or '?'.
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

def extract_links_from_pdf(pdf_path, start_page=6, end_page=309):
    """
    Iterate over pages start_page to end_page (1-indexed) of the PDF.
    Update the current category when a line exactly matches one of the expected category strings.
    Then, search for HTTP/HTTPS links using a regex.
    For each found link:
      - Resolve it via HTTP redirects.
      - Clean the resolved URL to obtain a direct manifest URI.
      - Store an object with two properties:
            "Manifest URI" and "Category".
    Only unique manifest URIs are included.
    """
    items = []
    current_category = "Uncategorized"
    seen = set()
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[start_page-1:end_page]:
            text = page.extract_text()
            if not text:
                continue
            # Update current category if any line matches one of the expected categories.
            for line in text.splitlines():
                line = line.strip()
                if line in CATEGORIES:
                    current_category = line
            # Regex to capture URLs with 8 or 9 digits and optional "?buttons=y"
            link_pattern = r"(http[s]?://\S*?nrs\.harvard\.edu\S*\d+(?:\?buttons=y)?)"
            found_links = re.findall(link_pattern, text)
            for link in found_links:
                resolved = resolve_redirect(link)
                if resolved:
                    manifest_uri = clean_manifest_url(resolved)
                    if manifest_uri and manifest_uri not in seen:
                        seen.add(manifest_uri)
                        items.append({
                            "Manifest URI": manifest_uri,
                            "Category": current_category
                        })
    return items

def main():
    metadata = extract_links_from_pdf(PDF_FILE, start_page=START_PAGE, end_page=END_PAGE)
    print(f"Extracted {len(metadata)} unique links with categories.")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    print(f"Saved metadata to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
