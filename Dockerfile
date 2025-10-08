# Use uv image directly to avoid multi-stage build issues
FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    chromium \
    graphicsmagick \
    poppler-utils \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    echo 'export CHROMIUM_FLAGS="$CHROMIUM_FLAGS --no-sandbox"' >> /etc/chromium.d/default-flags

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (this will recreate the venv in the container)
RUN rm -rf .venv && uv sync --frozen --no-dev

# Copy application code
COPY main.py ./
COPY browser/ ./browser/

# Set PATH to use virtual environment and ensure it's activated
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8001
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]