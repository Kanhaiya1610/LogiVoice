# LogiVoice 2.0 🚀
### AI-Powered Smart Logistics Assistant

LogiVoice 2.0 is a full-stack logistics automation platform built for the **JTP (Japan Third Party)** evaluation. It combines **Computer Vision (OCR)**, **Natural Language Processing (spaCy NER)**, and **Generative AI (Gemini)** to transform "dumb" logistics documents into searchable, chat-capable digital assets.

---

## 🏗 Architecture
```text
[ Frontend: React 19 ] <---> [ Backend: Flask API ]
       |                          |
       |                          +--> NLP: spaCy (Entity Recognition)
       |                          +--> ML: Scikit-Learn (Classification)
       |                          +--> GenAI: Google Gemini (Document Chat)
       v                          +--> OCR: Tesseract & PDFPlumber
[ Cloud: AWS S3 ] <-----------+   +--> Audio: FFmpeg & Whisper/Google
```

---

## ✨ Key Features

- 🧠 **Multi-Stage ML Pipeline**:
    - **Classification**: Naive Bayes model trained on expanded logistics datasets.
    - **Extraction**: spaCy NER (`en_core_web_sm`) to detect organizations and locations.
    - **Generative Chat**: Ask questions directly to your documents via integrated Gemini AI.
- 🎙️ **Voice Retrieval**: conversational voice commands to find invoices or shipping details.
- 📄 **Universal Parser**: Supports PDFs, Images (PNG/JPG), and Text files with automatic OCR.
- 📊 **Intelligence Dashboard**: Real-time analytics with SVG-rendered data visualizations.
- ☁️ **Enterprise Ready**: Dockerized deployment with optional AWS S3 cloud backup.
- 🌍 **JTP Optimized**: Built-in support for Japanese document translation and extraction.

---

## 🚀 Quick Start (Docker - Recommended)
```bash
docker-compose up --build
```
The app will be available at `http://localhost:5173`.

## 🛠 Manual Installation

### Backend
1. `cd backend`
2. `python -m venv venv`
3. `venv\Scripts\activate` (Windows)
4. `pip install -r requirements.txt`
5. `python -m spacy download en_core_web_sm`
6. `python app.py`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

---

## ⚙️ Environment Variables
Create a `.env` file in the `backend/` directory:
- `GEMINI_API_KEY`: Your Google AI Studio key (required for Chat feature).
- `AWS_ACCESS_KEY_ID`: Optional for S3 backup.
- `AWS_SECRET_ACCESS_KEY`: Optional for S3 backup.

---
*Developed for the JTP Innovation Evaluation Round. 2026.*
