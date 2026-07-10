/** @typedef {import('~/types/case').CaseInfo} CaseInfo */
/** @typedef {import('~/types/case').CaseStatus} CaseStatus */

const TERMINAL = new Set(['billable', 'mission', 'cancelled', 'skipped'])

/**
 * @param {CaseStatus} status
 * @returns {boolean}
 */
export function isTerminalStatus(status) {
  return TERMINAL.has(status)
}

/**
 * @param {CaseStatus} status
 * @returns {boolean}
 */
export function isIssueStatus(status) {
  return status === 'skipped'
}

/**
 * @param {{ minutes: number|null, mission: boolean, issueLocked?: boolean, currentStatus?: CaseStatus }} input
 * @returns {CaseStatus}
 */
export function statusFromCaseState({ minutes, mission, issueLocked = false, currentStatus }) {
  if (issueLocked && currentStatus === 'skipped') {
    return 'skipped'
  }
  if (minutes === 0) return 'cancelled'
  if (!Number.isInteger(minutes) || minutes < 0) return 'scheduled'
  if (mission) return 'mission'
  return 'billable'
}

/**
 * @param {CaseInfo} c
 */
export function applyStatusToCase(c) {
  if (isIssueStatus(c.status)) return
  c.status = statusFromCaseState({
    minutes: c.minutes,
    mission: c.mission,
    issueLocked: isIssueStatus(c.status),
    currentStatus: c.status
  })
}

/**
 * @typedef {{ icon: string|null, textClass: string, borderClass: string|null, opacityClass: string|null }} StatusDisplay
 */

/**
 * @param {CaseStatus} status
 * @returns {StatusDisplay}
 */
export function statusDisplayFromCase(status) {
  switch (status) {
    case 'billable':
      return {
        icon: 'i-lucide-check-circle-2',
        textClass: 'text-primary',
        borderClass: 'border-primary',
        opacityClass: 'opacity-90'
      }
    case 'mission':
      return {
        icon: 'i-lucide-heart',
        textClass: 'text-secondary',
        borderClass: 'border-secondary',
        opacityClass: 'opacity-90'
      }
    case 'cancelled':
      return {
        icon: 'i-lucide-x-circle',
        textClass: 'text-error',
        borderClass: 'border-error',
        opacityClass: 'opacity-70'
      }
    case 'skipped':
      return {
        icon: 'i-lucide-circle-alert',
        textClass: 'text-warning',
        borderClass: 'border-warning',
        opacityClass: 'opacity-80'
      }
    default:
      return {
        icon: null,
        textClass: 'text-highlighted',
        borderClass: null,
        opacityClass: null
      }
  }
}

/**
 * @param {CaseInfo[]} cases
 * @returns {CaseInfo[]}
 */
export function queueCases(cases) {
  return [...cases].sort((a, b) => a.case_pos - b.case_pos)
}

/**
 * @param {CaseInfo[]} cases
 * @returns {boolean}
 */
export function canSendToOffice(cases) {
  const q = queueCases(cases)
  return q.length > 0 && q.every(c => isTerminalStatus(c.status))
}

/**
 * @param {CaseInfo[]} cases
 */
function sumMinutes(cases) {
  return cases.reduce((sum, c) => sum + (c.minutes ?? 0), 0)
}

/**
 * @param {CaseInfo[]} cases
 */
export function sendSummary(cases) {
  const billable = cases.filter(c => c.status === 'billable')
  const mission = cases.filter(c => c.status === 'mission')
  const cancelled = cases.filter(c => c.status === 'cancelled')
  const issues = cases.filter(c => c.status === 'skipped')

  return {
    billableCount: billable.length,
    billableMinutes: sumMinutes(billable),
    missionCount: mission.length,
    missionMinutes: sumMinutes(mission),
    cancelledCount: cancelled.length,
    issueCount: issues.length
  }
}

/**
 * @param {CaseInfo[]} cases
 * @param {import('~/types/case').BillableCasesSubmissionResponse} response
 */
export function sendSummaryFromResponse(cases, response) {
  const updatedIds = new Set((response.updated ?? []).map(String))
  const confirmed = cases.filter(c => updatedIds.has(String(c.case_id)))
  return sendSummary(confirmed)
}

/**
 * @param {CaseInfo[]} cases
 * @returns {CaseInfo[]}
 */
export function serializeCasesForBillables(cases) {
  return queueCases(cases).map((caseItem) => {
    const payload = { ...caseItem }
    delete payload.mission
    return {
      ...payload,
      note: caseItem.note?.trim() ? caseItem.note : null,
      sub_status: caseItem.sub_status?.length ? caseItem.sub_status : null
    }
  })
}

/** @deprecated Billing page retained but unused */
export function billingReviewCases() {
  return []
}

/** @deprecated Billing page retained but unused */
export function canConfirmBilling() {
  return false
}

/** @deprecated Billing page retained but unused */
export function totalMinutes() {
  return 0
}
