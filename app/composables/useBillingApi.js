import { mockGetBillingSummaries } from '~/mock/billingStore'

export function useBillingApi() {
  async function getBillingSummaries() {
    return mockGetBillingSummaries()
  }

  return { getBillingSummaries }
}
