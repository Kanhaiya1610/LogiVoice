# LogiVoice: Smart Logistics Doc & Voice Assistant

LogiVoice is a modern web app that streamlines logistics document handling with AI-powered PDF extraction, voice commands, translation, barcode/QR detection, and annotation. It features a beautiful dashboard, bulk PDF processing, history tracking, and mobile-friendly design.

## Features
- Upload and preview multiple PDFs with auto document type detection (Invoice, Delivery Note, etc.)
- Extract key data (invoice number, customer, products) and detect barcodes/QR codes
- Translate extracted text to multiple languages
- Voice command support for searching and actions
- Annotate PDF previews and save as images
- Command/data history with CSV export and memory-saving auto-cleanup

## Setup
1. **Clone the repo:**
   ```bash
   git clone <your-repo-url>
   cd <project-folder>
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   - Install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and required language data files
   - Install [ffmpeg](https://ffmpeg.org/) and add to PATH (for voice feature)
3. **Run the app:**
   ```bash
   python app.py
   ```
4. **Open in browser:**
   Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Usage
- Upload one or more PDFs to see previews, extract data, translate, and annotate.
- Use the voice command button for smart search and actions.
- View and export your history, or clear it to free up space.

---

## 5-line Project Description for CV

Smart web app for logistics document automation: PDF upload, AI-powered data extraction, barcode/QR detection, and translation. Features voice command search, annotation, and bulk processing. Modern dashboard UI with history, export, and mobile support. Built with Python (Flask), JS, Bootstrap, Tesseract, and Google Translate. Designed for real-world logistics, document, and workflow efficiency. 