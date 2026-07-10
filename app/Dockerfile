# Medicafe UI — Nuxt 4 production image (api/ excluded via .dockerignore)
#
# Runtime only (set at deploy / compose — never as build ARG/ENV):
#   NUXT_PUBLIC_API_BASE → runtimeConfig.public.apiBase
#   NUXT_PUBLIC_API_KEY  → runtimeConfig.public.apiKey

FROM node:22-alpine AS deps
WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM deps AS build
COPY . .

RUN pnpm build

FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=8080

COPY --from=build /app/.output ./.output

EXPOSE 8080

CMD ["node", ".output/server/index.mjs"]
