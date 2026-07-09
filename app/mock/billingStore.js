import { clone, mockDelay } from '~/utils/duration'
import billingSummaries from '~/mock/billing-summaries.json'

/** @typedef {import('~/types/billing').BillingDaySummary} BillingDaySummary */

/** @returns {Promise<BillingDaySummary[]>} */
export async function mockGetBillingSummaries() {
  await mockDelay()
  return clone(billingSummaries).sort((a, b) => {
    const [am, ad, ay] = a.date.split('-').map(Number)
    const [bm, bd, by] = b.date.split('-').map(Number)
    const aTime = new Date(ay, am - 1, ad).getTime()
    const bTime = new Date(by, bm - 1, bd).getTime()
    return bTime - aTime
  })
}
