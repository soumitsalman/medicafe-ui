export default defineEventHandler((event) => {
  const config = useRuntimeConfig(event)
  const path = getRouterParam(event, 'path') || ''
  const requestUrl = getRequestURL(event)
  const target = new URL(path, `${config.apiProxyBase}/`)

  target.search = requestUrl.search

  return proxyRequest(event, target.toString())
})
