from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import pdfplumber
import speech_recognition as sr
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import subprocess
import tempfile
import cv2
import numpy as np
import json
import re
import shutil
import sys
import pickle
from datetime import datetime
from pyzbar.pyzbar import decode as barcode_decode
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator

# Optional dependencies handling
try:
    from dotenv import load_dotenv
    load_dotenv()
    HAS_DOTENV = True
except Exception:
    HAS_DOTENV = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import make_pipeline
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        nlp = spacy.load("en_core_web_sm")
    HAS_SPACY = True
except Exception as e:
    HAS_SPACY = False
    print(f"WARNING: spaCy failed to load: {e}")

try:
    import google.generativeai as genai
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        genai.configure(api_key=gemini_key)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        HAS_GEMINI = True
        print("Gemini AI configured successfully.")
    else:
        HAS_GEMINI = False
        print("WARNING: GEMINI_API_KEY not found in environment.")
except Exception as e:
    HAS_GEMINI = False
    print(f"WARNING: Gemini initialization error: {e}")

try:
    import boto3
    HAS_S3 = True
except Exception:
    HAS_S3 = False

# --- Backend Config ---
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PAGE_IMG_FOLDER = os.path.join(BASE_DIR, 'static', 'pdf_pages')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')

for folder in [UPLOAD_FOLDER, PAGE_IMG_FOLDER]:
    if not os.path.exists(folder): os.makedirs(folder)

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"!!! GLOBAL SERVER ERROR: {str(e)}")
    return jsonify({"error": str(e)}), 500

# --- ML CLASSIFIER ---
def train_ml_model():
    if not HAS_SKLEARN: return None
    model_path = os.path.join(BASE_DIR, 'doc_classifier.pkl')
    data = {
        "Invoice": [
            "invoice bill total amount due tax rate payment net 30 subtotal tax gst vat bank account", 
            "please pay total outstanding balance invoice summary order id reference bill to",
            "commercial invoice billing address remmitance advice invoice number INV purchase order",
            "invoice date subtotal discount grand total amount payable terms conditions"
        ],
        "Delivery Note": [
            "delivery note ship to dispatch date received items signature tracking pieces qty box packing", 
            "consignee address carrier waybill proof of delivery driver received in good condition",
            "dispatch slip goods received note delivery confirmation shipment weight package content",
            "received by date signature stamp delivery location tracking number courier"
        ],
        "Purchase Order": [
            "purchase order po number items requested vendor buyer authorized budget form unit price", 
            "official order requisition department procurement supply order contractual terms",
            "PO number vendor details buyer instructions item description quantity unit total cost",
            "authorized signature procurement officer purchase requisition internal order form"
        ],
        "Resume/CV": [
            "education experience skills resume cv profile project training internship university degree employment summary", 
            "work history objective certifications technical stack career summary achievements management skills",
            "professional experience key skills academic background languages spoken contact information summary",
            "projects personal details interests profile summary curriculum vitae experience overview"
        ]
    }
    texts, labels = [], []
    for label, samples in data.items():
        texts.extend(samples); labels.extend([label] * len(samples))
    model = make_pipeline(TfidfVectorizer(), MultinomialNB())
    model.fit(texts, labels)
    with open(model_path, 'wb') as f: pickle.dump(model, f)
    return model

doc_model = train_ml_model()

# --- EXTRACTION BRAIN ---
def clean_extracted_value(value, labels_to_strip):
    if not value: return 'N/A'
    cleaned = value.strip()
    prefixes = labels_to_strip + ['Name', 'No.', 'Number', ':', '.', '-', '#']
    changed = True
    while changed:
        original = cleaned
        for p in prefixes:
            cleaned = re.sub(rf'^{p}\s*[:.\-]*\s*', '', cleaned, flags=re.I).strip()
        if original == cleaned: changed = False
    noise_end = ['Customer', 'Address', 'Delivery', 'Product', 'Total', 'Ship', 'Bill', 'Date', 'Notes']
    for n in noise_end: cleaned = re.sub(rf'\s*{n}.*$', '', cleaned, flags=re.I).strip()
    return cleaned.strip(' :.-,#') if len(cleaned) > 0 else 'N/A'

def extract_smart_fields(text_block):
    inv_match = re.search(r'(?:Invoice|Bill|No|#)\s*[:.\-]?\s*([A-Z0-9\-\/]+)', text_block, re.I)
    inv = inv_match.group(1) if inv_match else 'N/A'
    
    name, addr = "N/A", "N/A"
    if HAS_SPACY:
        doc = nlp(text_block)
        orgs = [ent.text for ent in doc.ents if ent.label_ in ("ORG", "PERSON")]
        locs = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "FAC", "LOC")]
        name = orgs[0] if orgs else "N/A"
        addr = locs[0] if locs else "N/A"
    
    if name == "N/A":
        name_match = re.search(r'(?:Customer|Client|Bill To|Sold To)\s*[:.\-]?\s*(.+)', text_block, re.I)
        if name_match: name = clean_extracted_value(name_match.group(1), [])
    
    if addr == "N/A":
        addr_match = re.search(r'(?:Address|Ship To|Delivery)\s*[:.\-]?\s*(.+)', text_block, re.I)
        if addr_match: addr = clean_extracted_value(addr_match.group(1), [])
        
    return inv, name, addr

# --- ROUTES ---
@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    files = request.files.getlist('pdfFile')
    extracted_list = []
    for file in files:
        if not file.filename: continue
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        full_text, page_images, ext = "", [], os.path.splitext(file.filename)[1].lower()

        if ext == '.pdf':
            try:
                doc = fitz.open(filepath)
                for i in range(len(doc)):
                    img_name = f"{os.path.splitext(file.filename)[0]}_p{i+1}.png"
                    img_path = os.path.join(PAGE_IMG_FOLDER, img_name)
                    doc[i].get_pixmap(matrix=fitz.Matrix(2,2)).save(img_path)
                    page_images.append(f"/static/pdf_pages/{img_name}")
                doc.close()
                with pdfplumber.open(filepath) as pdf:
                    for page in pdf.pages: full_text += (page.extract_text() or "") + "\n"
            except: pass
        elif ext in ['.png', '.jpg', '.jpeg']:
            try:
                img = Image.open(filepath)
                full_text = pytesseract.image_to_string(img, lang='eng+jpn')
                img_name = f"{os.path.splitext(file.filename)[0]}_preview.png"
                img_path = os.path.join(PAGE_IMG_FOLDER, img_name)
                img.save(img_path); page_images.append(f"/static/pdf_pages/{img_name}")
            except: pass
        elif ext == '.txt':
            try: full_text = open(filepath, 'r', encoding='utf-8').read()
            except: pass

        blocks = re.split(r'(?=Invoice|Bill\s*To|Customer\s*Name)', full_text, flags=re.I)
        blocks = [b.strip() for b in blocks if len(b.strip()) > 30]
        if not blocks: blocks = [full_text]

        for block in blocks:
            inv, cust, addr = extract_smart_fields(block)
            if HAS_SKLEARN:
                pred = doc_model.predict([block.lower()])[0]
                prob = max(doc_model.predict_proba([block.lower()])[0])
                doc_type = f"{pred} ({round(prob*100, 1)}%)"
            else: doc_type = "Logistics Doc"
            
            data = {'id': datetime.now().timestamp(), 'filename': file.filename, 'doc_type': doc_type, 'invoice_number': inv, 'customer_name': cust, 'delivery_address': addr, 'img_url': page_images[0] if page_images else '', 'all_pages': page_images, 'full_text': block}
            extracted_list.append(data)
            
            # Persist history
            hist = []
            if os.path.exists(HISTORY_FILE):
                try: hist = json.load(open(HISTORY_FILE, 'r'))
                except: hist = []
            hist.append({'type': 'upload', 'timestamp': datetime.now().isoformat(), 'data': data})
            json.dump(hist, open(HISTORY_FILE, 'w'), indent=2)
            
    return jsonify({"success": True, "results": extracted_list})

@app.route('/api/chat', methods=['POST'])
def chat_with_doc():
    if not HAS_GEMINI: 
        print("Chat Error: Gemini not initialized.")
        return jsonify({"error": "Gemini AI not configured"}), 503
    
    data = request.json
    doc_text = data.get('document_text', '')
    question = data.get('question', '')
    
    if not doc_text:
        print("Chat Error: Document text is empty.")
        return jsonify({"error": "Document text is empty"}), 400

    print(f"Chatting with doc... Question: {question}")
    prompt = f"Document Content: {doc_text[:5000]}\n\nUser Question: {question}\n\nBased ONLY on the document provided, provide a short and accurate answer. If the information is not present, say 'I don't find this information in the document.'"
    
    try:
        response = gemini_model.generate_content(prompt)
        print("Gemini response received.")
        return jsonify({"answer": response.text})
    except Exception as e: 
        print(f"Gemini API Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/voice', methods=['POST'])
def voice_command():
    audio_file = request.files['audio']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as t_in:
        audio_file.save(t_in.name)
        t_out = t_in.name + '.wav'
    try:
        subprocess.run(['ffmpeg', '-y', '-i', t_in.name, '-ar', '16000', '-ac', '1', t_out], check=True, capture_output=True)
        recognizer = sr.Recognizer()
        with sr.AudioFile(t_out) as source:
            text = recognizer.recognize_google(audio_file=source)
    except: text = ""
    finally:
        for f in [t_in.name, t_out]:
            if os.path.exists(f): os.remove(f)
    return jsonify({'text': text})

@app.route('/api/history', methods=['GET'])
def get_history_route():
    if os.path.exists(HISTORY_FILE):
        try: return jsonify(json.load(open(HISTORY_FILE, 'r')))
        except: return jsonify([])
    return jsonify([])

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    if os.path.exists(HISTORY_FILE): json.dump([], open(HISTORY_FILE, 'w'))
    return jsonify({'status': 'cleared'})

@app.route('/static/<path:filename>')
def serve_static(filename): return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
