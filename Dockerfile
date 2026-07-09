# Medicafe UI — Nuxt 4 production image (api/ excluded via .dockerignore)

FROM node:22-alpine AS deps
WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM deps AS build
COPY . .

# Baked into the client bundle at build time; override at runtime with NUXT_PUBLIC_API_BASE
ARG CASES_BASE_URL=http://localhost:8000
ENV CASES_BASE_URL=${CASES_BASE_URL}

# Optional X-API-KEY sent to the API; baked at build time; override at runtime with NUXT_PUBLIC_API_KEY
ARG CASES_DB_API_KEY=
ENV CASES_DB_API_KEY=${CASES_DB_API_KEY}

RUN pnpm build

FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

COPY --from=build /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
