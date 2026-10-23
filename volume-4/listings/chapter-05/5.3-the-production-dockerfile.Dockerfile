# Applied AI Engineering, Volume IV, Chapter 5
# Section 5.3, Containerization with Docker
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# ─── Stage 1: Build dependencies ─────────────────────────────────────────────
FROM python:3.15-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (separate layer for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --target=/build/packages -r requirements.txt

# ─── Stage 2: Runtime image ───────────────────────────────────────────────────
FROM python:3.15-slim AS runtime

# Security: run as non-root user
RUN useradd --uid 10001 --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /build/packages /usr/local/lib/python3.15/site-packages

# Copy application code
COPY --chown=appuser:appuser src/ ./src/

# Switch to non-root user
USER appuser

# Expose port (documentation only; port binding is at runtime)
EXPOSE 8000

# Health check — probe the /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

# Start the application
CMD ["python", "-m", "uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-config", "src/logging_config.json"]
