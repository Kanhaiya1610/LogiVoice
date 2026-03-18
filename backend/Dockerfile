# Dockerfile for LogiVoice 2.0 Backend

FROM python:3.9-slim

# Install system dependencies required for OpenCV, Tesseract, FFmpeg, and ZBar
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-jpn \
    libtesseract-dev \
    ffmpeg \
    libzbar0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download spaCy model to avoid runtime downloads
RUN python -m spacy download en_core_web_sm

# Copy application files
COPY . .

# Set environment variables for tools inside the container
ENV TESSERACT_PATH=/usr/bin/tesseract
ENV FFMPEG_PATH=/usr/bin/ffmpeg
ENV FLASK_ENV=production
# Ensure python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1

# Expose backend port
EXPOSE 5000

# Start server using Gunicorn
# Using 4 workers for better performance
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
