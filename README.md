# LogiVoice 🚀
### AI-Powered Smart Logistics & Document Automation Assistant

LogiVoice is a sophisticated, full-stack automation platform designed to streamline logistics workflows. It leverages **Natural Language Processing (NLP)**, **Machine Learning (ML)**, and **Generative AI** to transform unstructured logistics documents (Invoices, Delivery Notes, Packing Slips) into actionable, searchable, and conversational digital assets.

---

## 🏗 Architecture
```text
[ User Interface ] <---> [ REST API ]
 (React + Vite)         (Flask + Python)
       |                       |
       |                       +--> NLP: spaCy (Entity Recognition)
       |                       +--> ML: Scikit-Learn (Classification)
       |                       +--> GenAI: Google Gemini (Interactive Chat)
       v                       +--> OCR: Tesseract & PDFPlumber
[ Cloud Storage ] <------------+   +--> Vision: OpenCV & ZBar (Barcodes)
   (AWS S3)                        +--> Audio: FFmpeg & SpeechRecognition
```

---

## ✨ Key Features

- 🧠 **Intelligence Engine**: 
    - **Automated Classification**: Scikit-Learn based Naive Bayes classifier identifies document types with high confidence.
    - **Named Entity Recognition (NER)**: spaCy-powered extraction of Organizations, Locations, and Dates.
    - **Conversational Document AI**: Integrated Gemini AI allows users to chat with their documents to extract specific details or summaries.
- 🎙️ **Voice Search Assistant**: Hands-free data retrieval using advanced speech-to-text processing for finding specific invoices or customer records.
- 📄 **Multi-Format Parsing**: Unified handling of PDFs, Images (PNG/JPG), and Text files with robust OCR capabilities.
- 📄 **Logical Document Splitting**: Intelligently identifies and separates multiple invoices or entries contained within a single consolidated file.
- 📊 **Dynamic Analytics**: Real-time dashboard featuring SVG data visualizations for document distribution and processing trends.
- 🌍 **Localization Ready**: Built-in translation engine supporting Japanese, Spanish, and Hindi.
- ☁️ **Enterprise Ready**: Full Docker containerization and optional AWS S3 integration for scalable storage.

---

## 🚀 Quick Start (Docker - Recommended)
The fastest way to deploy the entire stack:
```bash
docker-compose up --build
```
- Frontend: `http://localhost:80`
- Backend API: `http://localhost:5000`

## 🛠 Manual Installation

### Backend Setup
1. `cd backend`
2. `python -m venv venv`
3. Activate environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. `pip install -r requirements.txt`
5. `python -m spacy download en_core_web_sm`
6. `python app.py`

### Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev`

---

## ⚙️ Configuration
Create a `.env` file in the `backend/` directory based on `.env.example`:
- `GEMINI_API_KEY`: Required for the "Chat with Document" AI feature.
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: Optional for S3 cloud backups.

---
*LogiVoice — Intelligent Logistics Automation for the Modern Supply Chain.*
