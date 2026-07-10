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
    const loadId = `load_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
    // #region agent log
    fetch('http://127.0.0.1:7691/ingest/ceab04ba-7a84-4b90-b033-dde09e0fe1c6',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c1863d'},body:JSON.stringify({sessionId:'c1863d',location:'useCaseQueue.js:loadQueue:start',message:'loadQueue start',data:{loadId,prevCount:cases.value.length,importMetaServer:import.meta.server,importMetaClient:import.meta.client},timestamp:Date.now(),hypothesisId:'A,B,D'})}).catch(()=>{});
    // #endregion
    try {
      const fetched = await getCases()
      cases.value = fetched
      // #region agent log
      fetch('http://127.0.0.1:7691/ingest/ceab04ba-7a84-4b90-b033-dde09e0fe1c6',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c1863d'},body:JSON.stringify({sessionId:'c1863d',location:'useCaseQueue.js:loadQueue:success',message:'loadQueue success',data:{loadId,fetchedCount:Array.isArray(fetched)?fetched.length:'not-array',casesCount:cases.value.length},timestamp:Date.now(),hypothesisId:'A,E'})}).catch(()=>{});
      // #endregion
    } catch (err) {
      console.error('Failed to load schedule', err)
      // #region agent log
      fetch('http://127.0.0.1:7691/ingest/ceab04ba-7a84-4b90-b033-dde09e0fe1c6',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c1863d'},body:JSON.stringify({sessionId:'c1863d',location:'useCaseQueue.js:loadQueue:error',message:'loadQueue error',data:{loadId,errMsg:err?.message??String(err),prevCount:cases.value.length,preserved:cases.value.length>0},timestamp:Date.now(),hypothesisId:'B',runId:'post-fix'})}).catch(()=>{});
      // #endregion
      if (cases.value.length === 0) {
        cases.value = []
      }
    }
  }

  /**
   * @param {string} case_id
   * @param {Partial<Pick<CaseInfo, 'diagnosis' | 'minutes' | 'note'>>} fields
   */
  function updateCase(case_id, fields) {
    const c = cases.value.find(item => item.case_id === case_id)
    if (!c) return

    Object.assign(c, fields)

    if ('diagnosis' in fields) {
      const { cpt, eye } = deriveFromDx(c.diagnosis)
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

    c.status = 'skipped'
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
