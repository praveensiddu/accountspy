# syntax=docker/dockerfile:1
# Build a lightweight Python 3.13 image
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Install system deps for running (no build tools needed if wheels are available)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Only copy requirements first, to maximize docker layer cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend ./backend
COPY frontend ./frontend
COPY .env.example ./

# Expose app port
EXPOSE 8000

# Mandatory env variables (override at runtime)
# ACCOUNTS_DIR must be set to a mounted host directory
# CURRENT_YEAR must be set to the processing year
ENV ACCOUNTS_DIR="" \
    CURRENT_YEAR=""

# Start the FastAPI app with Uvicorn
# Note: backend/main.py mounts the static frontend at / and loads from env
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
