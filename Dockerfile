# Use Python 3.12 slim for smaller image
FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies (for chromadb, sentence-transformers, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY data/ ./data/
COPY .env ./.env

# Create directories for data and index
RUN mkdir -p chroma_db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the app
CMD ["python", "src/server/main.py"]