# PIP-Manuscripts-Processor

**PIP-Manuscripts-Processor** is a preprocessing pipeline designed for **Peirce’s manuscripts** and developed for the **Peirce Interprets Peirce** project.  
It automates the extraction of structured metadata, downloads IIIF manifests, and prepares manuscript images for further **diagram discovery and analysis**.

## Features
- Extracts metadata (titles, identifiers, links) from **Houghton Library’s Peirce manuscripts**
- Resolves IIIF manifest URIs and downloads the corresponding JSON files
- Organizes images and metadata into structured folders
- Generates JSON datasets for later **diagram recognition & analysis**

## Installation

```sh
git clone https://github.com/YOUR-USERNAME/PIP-Manuscripts-Processor.git
cd PIP-Manuscripts-Processor
pip install -r requirements.txt
