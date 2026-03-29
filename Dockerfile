FROM python:3.11.9-slim-bookworm

WORKDIR /app

# Install system dependencies needed by faiss-cpu and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer caching)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy project files
COPY . .

# Create non-root user and switch to it
RUN useradd -r -s /bin/false appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["python", "backend/server.py"]
