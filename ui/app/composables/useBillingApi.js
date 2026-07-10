import { apiFetchOptions } from '~/utils/apiFetch'
import { billingSummariesFromResponse } from '~/utils/billingSelectors'

export function useBillingApi() {
  const config = useRuntimeConfig()

  async function getBillingSummaries() {
    const data = await $fetch(
      `${config.public.apiBase}/cases/billables`,
      apiFetchOptions(config.public.apiKey)
    )
    return billingSummariesFromResponse(data)
  }

  return { getBillingSummaries }
}
