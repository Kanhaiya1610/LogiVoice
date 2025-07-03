from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
import pdfplumber
import speech_recognition as sr
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import subprocess
import tempfile
import pytesseract
from langdetect import detect, DetectorFactory
from googletrans import Translator
import json
from datetime import datetime
from pyzbar.pyzbar import decode as barcode_decode
import cv2
import numpy as np
DetectorFactory.seed = 0
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\KISHAN\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Store extracted data in memory for now
extracted_data = {}
pdf_text = ''

PAGE_IMG_FOLDER = os.path.join('static', 'pdf_pages')
if not os.path.exists(PAGE_IMG_FOLDER):
    os.makedirs(PAGE_IMG_FOLDER)

page_images = []  # List of image URLs for the current PDF

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

HISTORY_FILE = 'history.json'

def save_history(entry):
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []
    except Exception:
        history = []
    history.append(entry)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_history():
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def clear_history():
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)
    # Remove all files in uploads and static/pdf_pages
    for folder in [UPLOAD_FOLDER, PAGE_IMG_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass

def is_mostly_ascii(s, threshold=0.8):
    ascii_count = sum(1 for c in s if ord(c) < 128)
    return ascii_count / max(1, len(s)) >= threshold

def detect_doc_type(text):
    text_lower = text.lower()
    if 'invoice' in text_lower:
        return 'Invoice'
    elif 'delivery note' in text_lower or 'delivery slip' in text_lower:
        return 'Delivery Note'
    elif 'packing list' in text_lower:
        return 'Packing List'
    elif 'receipt' in text_lower:
        return 'Receipt'
    else:
        return 'Unknown'

@app.route('/')
def index():
    return render_template('index.html', extracted=extracted_data, pdf_text=pdf_text, page_images=page_images)

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    global extracted_data, pdf_text, page_images
    page_images = []
    files = request.files.getlist('pdfFile')
    extracted_list = []
    preview_cards = []
    if not files or files[0].filename == '':
        return redirect(url_for('index'))
    for file in files:
        if file and file.filename:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            # Render first page as image for preview and barcode detection
            doc = fitz.open(filepath)
            base_name = os.path.splitext(file.filename)[0]
            img_url = ''
            barcodes = []
            for i, page in enumerate(doc):
                if i == 0:
                    zoom = 2
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    img_path = os.path.join(PAGE_IMG_FOLDER, f'{base_name}_page_{i+1}.png')
                    pix.save(img_path)
                    img_url = '/static/pdf_pages/' + f'{base_name}_page_{i+1}.png'
                    # Barcode/QR detection
                    img_cv = cv2.imread(img_path)
                    if img_cv is not None:
                        detected = barcode_decode(img_cv)
                        for code in detected:
                            barcodes.append({'type': code.type, 'value': code.data.decode('utf-8', errors='ignore')})
                    break
            preview_cards.append({'filename': file.filename, 'img_url': img_url})
            # Extract text (with OCR fallback, no filtering)
            with pdfplumber.open(filepath) as pdf:
                all_text = []
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if not text:
                        im = page.to_image(resolution=300).original
                        ocr_text = pytesseract.image_to_string(im, lang='eng+jpn+hin+spa+chi_sim+por+ara')
                        all_text.append(ocr_text)
                    else:
                        all_text.append(text)
                text = "\n".join(all_text)
            doc_type = detect_doc_type(text)
            # Simple extraction logic (can be improved with regex/templates)
            import re
            invoice_number = re.search(r'Invoice\s*No\.?\s*:?\s*(\w+)', text, re.IGNORECASE)
            customer_name = re.search(r'Customer\s*Name\s*:?\s*([\w\s]+)', text, re.IGNORECASE)
            delivery_address = re.search(r'Delivery\s*Address\s*:?\s*([\w\s,.-]+)', text, re.IGNORECASE)
            # Dummy product list extraction (improve as needed)
            product_list = []
            for match in re.finditer(r'(\w[\w\s]+)\s+(\d+)\s+pcs', text):
                product_list.append({'item': match.group(1).strip(), 'quantity': match.group(2)})
            data = {
                'invoice_number': invoice_number.group(1) if invoice_number else '',
                'customer_name': customer_name.group(1).strip() if customer_name else '',
                'delivery_address': delivery_address.group(1).strip() if delivery_address else '',
                'product_list': product_list,
                'doc_type': doc_type,
                'barcodes': barcodes
            }
            extracted_list.append({'filename': file.filename, 'data': data, 'doc_type': doc_type, 'img_url': img_url, 'barcodes': barcodes})
            preview_cards.append({'filename': file.filename, 'img_url': img_url, 'doc_type': doc_type, 'barcodes': barcodes})
            # Save to history
            save_history({
                'type': 'pdf',
                'filename': file.filename,
                'timestamp': datetime.now().isoformat(),
                'extracted_data': data,
                'pdf_text': text,
                'doc_type': doc_type,
                'barcodes': barcodes
            })
            # For the first file, set extracted_data/pdf_text for dashboard display
            if files.index(file) == 0:
                extracted_data = data
                pdf_text = text
    return render_template('index.html', extracted=extracted_data, pdf_text=pdf_text, page_images=page_images, extracted_list=extracted_list, preview_cards=preview_cards)

@app.route('/voice_command', methods=['POST'])
def voice_command():
    if 'audio' not in request.files:
        return jsonify({'text': ''})
    audio_file = request.files['audio']
    # Save uploaded audio to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_in:
        audio_file.save(temp_in)
        temp_in_path = temp_in.name
    # Convert to WAV using ffmpeg
    temp_out = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_out_path = temp_out.name
    temp_out.close()
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', temp_in_path, '-ar', '16000', '-ac', '1', temp_out_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_out_path) as source:
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
        except Exception as e:
            text = ''
    except Exception as e:
        text = ''
    finally:
        import os
        os.remove(temp_in_path)
        os.remove(temp_out_path)

    # Voice-to-action logic
    import re
    result = None
    if text:
        # Search for invoice number
        invoice_match = re.search(r'(invoice|find invoice|show invoice)\s*(\d+)', text, re.IGNORECASE)
        if invoice_match:
            invoice_no = invoice_match.group(2)
            for inv in extracted_data.get('invoices', []):
                if inv['invoice_number'] == invoice_no:
                    result = {
                        'type': 'invoice',
                        'data': inv
                    }
                    break
        # Search for customer name
        customer_match = re.search(r'(customer|find customer|show deliveries for|show customer)\s*([\w\s]+)', text, re.IGNORECASE)
        if customer_match:
            customer_name = customer_match.group(2).strip().lower()
            matches = [inv for inv in extracted_data.get('invoices', []) if inv['customer_name'].lower() == customer_name]
            if matches:
                result = {
                    'type': 'customer',
                    'data': matches
                }
    # Save to history
    save_history({
        'type': 'voice',
        'timestamp': datetime.now().isoformat(),
        'recognized_text': text,
        'result': result
    })
    return jsonify({'text': text, 'result': result})

@app.route('/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    text = data.get('text', '')
    target = data.get('target', 'en')
    translator = Translator()
    try:
        translated = translator.translate(text, dest=target).text
    except Exception as e:
        translated = 'Translation failed.'
    return jsonify({'translated': translated})

@app.route('/translate_file', methods=['POST'])
def translate_file():
    data = request.get_json()
    filename = data.get('filename')
    target = data.get('target', 'en')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'translated': 'File not found.'})
    # Extract all text from the PDF
    with pdfplumber.open(filepath) as pdf:
        all_text = []
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                im = page.to_image(resolution=300).original
                ocr_text = pytesseract.image_to_string(im, lang='eng+jpn+hin+spa+chi_sim+por+ara')
                all_text.append(ocr_text)
            else:
                all_text.append(text)
        text = "\n".join(all_text)
    from googletrans import Translator
    translator = Translator()
    try:
        translated = translator.translate(text, dest=target).text
    except Exception as e:
        translated = 'Translation failed.'
    return jsonify({'translated': translated})

@app.route('/extract_file', methods=['POST'])
def extract_file():
    data = request.get_json()
    filename = data.get('filename')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found.'})
    # Extract all text from the PDF
    with pdfplumber.open(filepath) as pdf:
        all_text = []
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                im = page.to_image(resolution=300).original
                ocr_text = pytesseract.image_to_string(im, lang='eng+jpn+hin+spa+chi_sim+por+ara')
                all_text.append(ocr_text)
            else:
                all_text.append(text)
        text = "\n".join(all_text)
    import re
    invoice_number = re.search(r'Invoice\s*No\.?\s*:?\s*(\w+)', text, re.IGNORECASE)
    customer_name = re.search(r'Customer\s*Name\s*:?\s*([\w\s]+)', text, re.IGNORECASE)
    delivery_address = re.search(r'Delivery\s*Address\s*:?\s*([\w\s,.-]+)', text, re.IGNORECASE)
    product_list = []
    for match in re.finditer(r'(\w[\w\s]+)\s+(\d+)\s+pcs', text):
        product_list.append({'item': match.group(1).strip(), 'quantity': match.group(2)})
    return jsonify({
        'invoice_number': invoice_number.group(1) if invoice_number else '',
        'customer_name': customer_name.group(1).strip() if customer_name else '',
        'delivery_address': delivery_address.group(1).strip() if delivery_address else '',
        'product_list': product_list
    })

@app.route('/history', methods=['GET'])
def history():
    return jsonify(get_history())

@app.route('/clear_history', methods=['POST'])
def clear_history_route():
    clear_history()
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    app.run(debug=True) 