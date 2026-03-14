# Sustainability & SDG Reporting Hub — Backend API
# Multi-stage build for smaller image (optional: use single stage for simplicity)

FROM python:3.12-slim

WORKDIR /app

# Install system deps for PostgreSQL client (if needed by drivers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
RUN pip install "poetry==$POETRY_VERSION"

# Copy dependency files first (better layer caching)
COPY pyproject.toml poetry.lock* ./

# Install dependencies (include dev group so pytest works in container)
RUN poetry install --no-root

# Copy application code
COPY . .

# Run as non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Ensure app package is importable when running uvicorn/alembic
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Default: run uvicorn with app.main:app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
