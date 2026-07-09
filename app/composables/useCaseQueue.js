import { deriveFromDx } from '~/utils/dxLookup'
import {
  applyStatusToCase,
  isIssueStatus
} from '~/utils/caseSelectors'

/** @typedef {import('~/types/case').CaseInfo} CaseInfo */
/** @typedef {import('~/types/case').IssueType} IssueType */

export function useCaseQueue() {
  const cases = useState('caseQueue', () => /** @type {CaseInfo[]} */ ([]))
  const { getCases, sendToOffice: apiSendToOffice } = useCaseApi()

  async function loadQueue() {
    try {
      cases.value = await getCases()
    } catch (err) {
      console.error('Failed to load schedule', err)
      cases.value = []
    }
  }

  /**
   * @param {string} case_id
   * @param {Partial<Pick<CaseInfo, 'dx' | 'minutes' | 'note'>>} fields
   */
  function updateCase(case_id, fields) {
    const c = cases.value.find(item => item.case_id === case_id)
    if (!c) return

    Object.assign(c, fields)

    if ('dx' in fields) {
      const { cpt, eye } = deriveFromDx(c.dx)
      c.cpt = cpt
      c.eye = eye
    }

    if (!isIssueStatus(c.status)) {
      applyStatusToCase(c)
    }
  }

  /**
   * @param {string} case_id
   * @param {boolean} checked
   */
  function setMission(case_id, checked) {
    const c = cases.value.find(item => item.case_id === case_id)
    if (!c || isIssueStatus(c.status)) return

    c.mission = checked
    applyStatusToCase(c)
  }

  /** @param {string} case_id */
  function cancelCase(case_id) {
    const c = cases.value.find(item => item.case_id === case_id)
    if (!c || isIssueStatus(c.status)) return

    c.minutes = 0
    c.mission = false
    c.status = 'cancelled'
  }

  /** @param {string} case_id */
  function undoCase(case_id) {
    const c = cases.value.find(item => item.case_id === case_id)
    if (!c) return

    c.minutes = null
    c.mission = false
    c.note = ''
    c.sub_status = []
    c.status = 'scheduled'
  }

  /**
   * @param {string} case_id
   * @param {{ sub_status: IssueType[], note?: string }} payload
   */
  function reportIssue(case_id, { sub_status, note = '' }) {
    const c = cases.value.find(item => item.case_id === case_id)
    if (!c) return

    c.status = 'issue'
    c.sub_status = [...sub_status]
    c.note = note
  }

  async function sendToOffice() {
    try {
      const snapshot = [...cases.value]
      const result = await apiSendToOffice(snapshot)
      cases.value = []
      return result
    } catch (err) {
      console.error('Failed to send to office', err)
      throw err
    }
  }

  return {
    cases,
    loadQueue,
    updateCase,
    setMission,
    cancelCase,
    undoCase,
    reportIssue,
    sendToOffice
  }
}
