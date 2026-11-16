# --- front ---
FROM node:22-alpine AS front
WORKDIR /front
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- app ---
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/pyproject.toml ./
RUN python -c "import tomllib;print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > requirements.txt \
 && pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY puzzles ./puzzles
COPY --from=front /front/dist ./static
RUN useradd --uid 10001 --no-create-home app && mkdir /data && chown app /data
USER app
VOLUME /data
EXPOSE 8000
# One worker: SQLite + in-memory rate limiter. Behind your proxy/tunnel, trust X-Forwarded-*.
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
