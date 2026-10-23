FROM python:3.15-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --target=/build/packages -r requirements.txt

FROM python:3.15-slim AS runtime

RUN useradd --uid 10001 --create-home --shell /bin/bash appuser
WORKDIR /app

COPY --from=builder /build/packages /usr/local/lib/python3.15/site-packages
COPY --chown=appuser:appuser app/ ./app/

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
