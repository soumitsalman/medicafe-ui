/** @param {string | undefined} apiKey */
export function apiFetchOptions(apiKey) {
  if (!apiKey) {
    return {}
  }

  return {
    headers: {
      'X-API-KEY': apiKey
    }
  }
}
