# Multi-stage build for optimized image size
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages with C extensions
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ build-essential && rm -rf /var/lib/apt/lists

# Copy requirements.txt and build python dependencies, using wheel packages
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ============================================
# Production stage
# ============================================
FROM python:3.11-slim

# Add non-root user for safety when running the container
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

# Copy dependencies from wheel directory and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code and set user to appuser
COPY --chown=appuser:appuser ./app ./app
# Set a dedicated cache directory within the /app volume for HuggingFace/Sentence-Transformers models
ENV HF_HOME=/app/.hf_cache
RUN mkdir -p ${HF_HOME} && chown -R appuser:appuser ${HF_HOME}
USER appuser

# Set Python path
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]