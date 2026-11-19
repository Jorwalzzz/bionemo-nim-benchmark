# syntax=docker/dockerfile:1

# -----------------------------------------------------------------------------
# Stage 1: Build virtual environment with dependencies
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build prerequisites for C-extensions/wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtualenv to isolate installed packages
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install package dependencies first for layer caching
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# -----------------------------------------------------------------------------
# Stage 2: Minimal runtime image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runner

# Install runtime system libraries required by RDKit, Matplotlib, and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libxrender1 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8088

# Create non-root unprivileged service user
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -d /home/appuser -m -s /bin/bash appuser

WORKDIR /app

# Copy application repository files with appuser ownership
COPY --chown=appuser:appuser . .

# Ensure runtime directories exist and are writable by appuser
RUN mkdir -p /app/results /app/data/pdbs && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8088/api/health || exit 1

CMD ["python", "serve_cockpit.py", "--host", "0.0.0.0", "--port", "8088"]
