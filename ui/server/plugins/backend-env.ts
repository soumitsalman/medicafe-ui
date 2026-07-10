/**
 * Map deploy-time BACKEND_* env vars onto runtimeConfig.public.
 * Never set these as Docker build ARG/ENV — only at container/process start.
 */
export default defineNitroPlugin(() => {
  const config = useRuntimeConfig()

  if (process.env.BACKEND_BASE_URL) {
    config.public.apiBase = process.env.BACKEND_BASE_URL
  }
  if (process.env.BACKEND_API_KEY !== undefined) {
    config.public.apiKey = process.env.BACKEND_API_KEY
  }
})
