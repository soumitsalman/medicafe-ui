# Medicafe API — FastAPI production image

FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CASES_DB_PATH=/data/cases.duckdb

# Optional API key gate (X-API-KEY header). Prefer CASES_DB_API_KEY; legacy API_KEY is still accepted.
# Set at runtime, e.g. docker run -e CASES_DB_API_KEY=your-secret ...

RUN mkdir -p /data

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

EXPOSE 8000

# https://fastapi.tiangolo.com/deployment/docker/
CMD ["fastapi", "run", "main.py", "--port", "8000"]
