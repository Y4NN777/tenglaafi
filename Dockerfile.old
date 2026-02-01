# Use Python 3.12 slim for smaller image
FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY data/ ./data/

# Create directories for data and index
RUN mkdir -p chroma_db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the app
CMD ["python", "-m", "src.server.main"]
