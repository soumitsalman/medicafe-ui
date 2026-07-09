/** @typedef {import('~/types/case').CaseDto} CaseDto */
/** @typedef {import('~/types/case').CaseStatus} CaseStatus */
/** @typedef {import('~/types/case').SendingPayloadDto} SendingPayloadDto */

const TERMINAL = new Set(['completed', 'mission', 'cancelled', 'issue'])

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
  return status === 'issue'
}

/**
 * @param {{ minutes: number|null, mission: boolean, issueLocked?: boolean, currentStatus?: CaseStatus }} input
 * @returns {CaseStatus}
 */
export function statusFromCaseState({ minutes, mission, issueLocked = false, currentStatus }) {
  if (issueLocked && currentStatus === 'issue') {
    return 'issue'
  }
  if (!Number.isInteger(minutes) || minutes < 0) return 'pending'
  if (minutes === 0) return 'cancelled'
  if (mission) return 'mission'
  return 'completed'
}

/**
 * @param {CaseDto} c
 */
export function applyStatusToCase(c) {
  if (isIssueStatus(c.status)) return
  c.status = statusFromCaseState({
    minutes: c.minutes,
    mission: c.mission,
    issueLocked: true,
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
    case 'completed':
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
    case 'issue':
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
 * @param {CaseDto[]} cases
 * @returns {CaseDto[]}
 */
export function queueCases(cases) {
  return [...cases].sort((a, b) => a.pos - b.pos)
}

/**
 * @param {CaseDto[]} cases
 * @returns {boolean}
 */
export function canSendToOffice(cases) {
  const q = queueCases(cases)
  return q.length > 0 && q.every(c => isTerminalStatus(c.status))
}

/**
 * @param {CaseDto[]} cases
 */
function sumMinutes(cases) {
  return cases.reduce((sum, c) => sum + (c.minutes ?? 0), 0)
}

/**
 * @param {CaseDto[]} cases
 */
export function sendSummary(cases) {
  const completed = cases.filter(c => c.status === 'completed')
  const mission = cases.filter(c => c.status === 'mission')
  const cancelled = cases.filter(c => c.status === 'cancelled')
  const issues = cases.filter(c => c.status === 'issue')

  return {
    billableCount: completed.length,
    billableMinutes: sumMinutes(completed),
    missionCount: mission.length,
    missionMinutes: sumMinutes(mission),
    cancelledCount: cancelled.length,
    issueCount: issues.length
  }
}

/**
 * @param {CaseDto[]} cases
 * @returns {SendingPayloadDto}
 */
export function serializeCasesForSend(cases) {
  const q = queueCases(cases)
  const date = q[0]?.date ?? ''
  return {
    date,
    rows: q.map((c) => {
      /** @type {import('~/types/case').SendingRowDto} */
      const row = {
        patient_id: c.patientId,
        status: /** @type {Exclude<CaseStatus, 'pending'>} */ (c.status),
        minutes: c.minutes,
        dx: c.dx,
        cpt: c.cpt,
        eye: c.eye,
        note: c.note ?? ''
      }
      if (c.status === 'issue') {
        row.sub_state = c.subState ?? []
      }
      return row
    })
  }
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
export function totalDurationMinutes() {
  return 0
}
