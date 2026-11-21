FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock.txt ./
RUN python -m pip install --no-cache-dir -r requirements.lock.txt \
    && python -m pip check
COPY database/ database/
COPY backend/ backend/
COPY frontend/ frontend/
COPY scripts/ scripts/
COPY tests/ tests/
USER 65534:65534
CMD ["python", "-m", "scripts.seed"]
