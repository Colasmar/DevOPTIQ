# Dockerfile — AFDEC / Flask → Cloud Run
FROM python:3.12-slim

# 1) Dépendances système de base
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && rm -rf /var/lib/apt/lists/*

# 2) Répertoire de travail
WORKDIR /app

# 3) Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install gunicorn

# 4) Code
COPY . .

# 5) Gunicorn écoute sur $PORT pour Cloud Run
ENV PORT=8080
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8080", "Code.app:app"]
