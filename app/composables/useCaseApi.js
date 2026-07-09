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
      summary: sendSummaryFromResponse(cases, response)
    }
  }

  return {
    getCases,
    sendToOffice
  }
}
