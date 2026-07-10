import { apiFetchOptions } from '~/utils/apiFetch'
import {
  sendSummaryFromResponse,
  serializeCasesForBillables
} from '~/utils/caseSelectors'

/** @typedef {import('~/types/case').CaseInfo} CaseInfo */

export function useCaseApi() {
  const config = useRuntimeConfig()

  async function getCases() {
    /** @type {CaseInfo[]} */
    const data = await $fetch(
      `${config.public.apiBase}/cases/schedules`,
      apiFetchOptions(config.public.apiKey)
    )
    // #region agent log
    fetch('http://127.0.0.1:7691/ingest/ceab04ba-7a84-4b90-b033-dde09e0fe1c6',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'c1863d'},body:JSON.stringify({sessionId:'c1863d',location:'useCaseApi.js:getCases',message:'getCases response',data:{isArray:Array.isArray(data),count:Array.isArray(data)?data.length:null,apiBase:config.public.apiBase,hasApiKey:!!config.public.apiKey},timestamp:Date.now(),hypothesisId:'B,E'})}).catch(()=>{});
    // #endregion
    return data.map(c => ({
      ...c,
      mission: false,
      sub_status: c.sub_status ?? [],
      note: c.note ?? ''
    }))
  }

  /**
   * @param {CaseInfo[]} cases
   */
  async function sendToOffice(cases) {
    const payload = serializeCasesForBillables(cases)

    const response = await $fetch(`${config.public.apiBase}/cases/billables`, {
      method: 'POST',
      body: payload,
      ...apiFetchOptions(config.public.apiKey)
    })
    return {
      payload,
      summary: sendSummaryFromResponse(payload, response)
    }
  }

  return {
    getCases,
    sendToOffice
  }
}
