# Medicafe merged runtime: Nuxt public server + internal FastAPI server

FROM node:22-bookworm-slim AS ui-build
WORKDIR /ui

ENV CI=true

RUN corepack enable

COPY ui/package.json ui/pnpm-lock.yaml ui/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY ui/ .
RUN pnpm build

FROM python:3.12-slim AS runner
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CASES_DB_PATH=/data
ENV NODE_ENV=production
ENV UI_HOST=0.0.0.0
ENV UI_PORT=8080
ENV API_HOST=127.0.0.1
ENV API_PORT=9000
ENV NUXT_PUBLIC_API_BASE=/api

RUN apt-get update \
  && apt-get install -y --no-install-recommends bash ca-certificates libstdc++6 \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /data

COPY --from=node:22-bookworm-slim /usr/local /usr/local

COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/api/requirements.txt

COPY api/ /app/api/
COPY --from=ui-build /ui/.output /app/ui/.output
COPY entrypoint.sh /app/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["bash", "/app/entrypoint.sh"]
