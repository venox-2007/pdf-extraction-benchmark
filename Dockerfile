FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src
COPY scripts ./scripts
COPY tests ./tests
COPY config ./config

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e . \
    && pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "pdf_extraction_benchmark.main"]
