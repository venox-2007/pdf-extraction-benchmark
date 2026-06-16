FROM python:3.11-slim

WORKDIR /app

# System dependencies:
# - default-jre: required by OpenDataLoader (Java-based PDF extraction)
# - tesseract-ocr: required by TesseractExtractor
# - libglib2.0-0 libgl1: required by OpenCV (PaddleOCR dependency)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre \
    tesseract-ocr \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src
COPY scripts ./scripts
COPY config ./config

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e . \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "src/pdf_extraction_benchmark/ui/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]
