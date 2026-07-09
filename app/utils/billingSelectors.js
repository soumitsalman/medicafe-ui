import { format, parse } from 'date-fns'

/** @typedef {import('~/types/case').CaseInfo} CaseInfo */
/** @typedef {import('~/types/billing').BillingDaySummary} BillingDaySummary */

/**
 * Format ISO service_date (YYYY-MM-DD) → MM-dd-yyyy for BillingSummaryCard.
 * @param {string} serviceDate
 */
export function formatBillingCardDate(serviceDate) {
  const d = parse(serviceDate, 'yyyy-MM-dd', new Date())
  return format(d, 'MM-dd-yyyy')
}

/**
 * Aggregate GET /cases/billables response into BillingDaySummary[] (newest-first).
 * @param {{ cases?: CaseInfo[] } | CaseInfo[]} response
 * @returns {BillingDaySummary[]}
 */
export function billingSummariesFromResponse(response) {
  const cases = Array.isArray(response) ? response : (response?.cases ?? [])

  /** @type {Map<string, BillingDaySummary>} */
  const byDate = new Map()

  for (const c of cases) {
    const iso = c.service_date
    if (!iso) continue

    if (!byDate.has(iso)) {
      byDate.set(iso, {
        date: formatBillingCardDate(iso),
        billedHours: 0,
        nonBilledHours: 0,
        cancelledCount: 0,
        issueCount: 0
      })
    }

    const summary = byDate.get(iso)
    const minutes = Number(c.minutes) || 0

    if (c.status === 'billable') {
      summary.billedHours += minutes / 60
    } else if (c.status === 'mission') {
      summary.nonBilledHours += minutes / 60
    } else if (c.status === 'cancelled') {
      summary.cancelledCount += 1
    } else if (c.status === 'issue') {
      summary.issueCount += 1
    }
  }

  return [...byDate.entries()]
    .sort(([a], [b]) => (a < b ? 1 : a > b ? -1 : 0))
    .map(([, summary]) => summary)
}
