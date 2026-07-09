import { clone, mockDelay } from '~/utils/duration'
import { deriveFromDx } from '~/utils/dxLookup'
import {
  applyStatusToCase,
  sendSummary,
  serializeCasesForSend,
  statusFromCaseState
} from '~/utils/caseSelectors'
import receiving from '~/mock/receiving.json'
import receivingBusy from '~/mock/receiving-busy.json'
import receivingMinimal from '~/mock/receiving-minimal.json'
import receivingPendingOnly from '~/mock/receiving-pending-only.json'

/** @type {Record<string, typeof receiving>} */
export const MOCK_FIXTURES = {
  default: receiving,
  busy: receivingBusy,
  minimal: receivingMinimal,
  'pending-only': receivingPendingOnly
}

/** Active fixture key — change to swap mock input during dev */
const ACTIVE_FIXTURE = 'default'

/** @typedef {import('~/types/case').CaseDto} CaseDto */
/** @typedef {import('~/types/case').IssueType} IssueType */
/** @typedef {import('~/types/case').SendingPayloadDto} SendingPayloadDto */

/**
 * @param {import('~/mock/receiving.json').rows[number]} row
 * @param {string} date
 * @returns {CaseDto}
 */
function mapRow(row, date) {
  const { cpt, eye } = deriveFromDx(row.dx)
  const minutes = Number.isInteger(row.minutes) ? row.minutes : null
  return {
    id: `${date}:${row.patient_id}`,
    date,
    pos: row.pos,
    patientId: row.patient_id,
    name: row.name,
    dob: row.dob,
    dx: row.dx,
    cpt: cpt || row.cpt,
    eye: eye || row.eye,
    minutes,
    mission: false,
    note: '',
    subState: [],
    status: statusFromCaseState({ minutes, mission: false })
  }
}

function getActiveReceiving() {
  return MOCK_FIXTURES[ACTIVE_FIXTURE] ?? receiving
}

function buildInitialCases() {
  const source = getActiveReceiving()
  return source.rows.map(row => mapRow(row, source.date))
}

/** @type {CaseDto[]} */
let cases = clone(buildInitialCases())

/** @type {SendingPayloadDto[]} */
let sentLog = []

/** @returns {Promise<CaseDto[]>} */
export async function mockGetCases() {
  await mockDelay()
  return clone(cases)
}

/**
 * @param {string} caseId
 * @param {Partial<Pick<CaseDto, 'dx' | 'minutes' | 'mission' | 'note'>>} fields
 * @returns {Promise<CaseDto>}
 */
export async function mockPatchCase(caseId, fields) {
  await mockDelay(150)
  const c = cases.find(item => item.id === caseId)
  if (!c) throw createError({ statusCode: 404, message: 'Case not found' })

  Object.assign(c, fields)

  if ('dx' in fields) {
    const { cpt, eye } = deriveFromDx(c.dx)
    c.cpt = cpt
    c.eye = eye
  }

  applyStatusToCase(c)
  return clone(c)
}

/** @param {string} caseId */
export async function mockCancelCase(caseId) {
  await mockDelay()
  const c = cases.find(item => item.id === caseId)
  if (!c) throw createError({ statusCode: 404, message: 'Case not found' })

  c.minutes = 0
  c.mission = false
  applyStatusToCase(c)
  return clone(c)
}

/** @param {string} caseId */
export async function mockUndoCase(caseId) {
  await mockDelay()
  const c = cases.find(item => item.id === caseId)
  if (!c) throw createError({ statusCode: 404, message: 'Case not found' })

  c.minutes = null
  c.mission = false
  c.note = ''
  c.subState = []
  c.status = 'pending'
  return clone(c)
}

/**
 * @param {string} caseId
 * @param {{ subState: IssueType[], note?: string }} payload
 */
export async function mockReportIssue(caseId, { subState, note = '' }) {
  await mockDelay()
  const c = cases.find(item => item.id === caseId)
  if (!c) throw createError({ statusCode: 404, message: 'Case not found' })

  c.status = 'issue'
  c.subState = [...subState]
  c.note = note
  return clone(c)
}

/** @returns {Promise<{ payload: SendingPayloadDto, summary: ReturnType<typeof sendSummary> }>} */
export async function mockSendToOffice() {
  await mockDelay()
  const snapshot = clone(cases)
  snapshot.forEach(applyStatusToCase)

  const payload = serializeCasesForSend(snapshot)
  const summary = sendSummary(snapshot)

  sentLog.push(clone(payload))
  cases = []
  return { payload, summary }
}

/** Reset mock data to initial state */
export async function mockResetStore() {
  cases = clone(buildInitialCases())
  sentLog = []
  return clone(cases)
}

export const MOCK_DATE = getActiveReceiving().date
