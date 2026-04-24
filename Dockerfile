FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Minimal runtime libraries for OpenCV / scientific wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app
COPY ml ./ml

RUN mkdir -p outputs logs

EXPOSE 5000

CMD ["gunicorn", "--factory", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "app.app:create_app"]
