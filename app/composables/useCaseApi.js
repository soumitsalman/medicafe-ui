import {
  mockGetCases,
  mockPatchCase,
  mockCancelCase,
  mockUndoCase,
  mockReportIssue,
  mockSendToOffice,
  mockResetStore
} from '~/mock/store'

export function useCaseApi() {
  async function getCases() {
    return mockGetCases()
  }

  async function patchCase(caseId, fields) {
    return mockPatchCase(caseId, fields)
  }

  async function cancelCase(caseId) {
    return mockCancelCase(caseId)
  }

  async function undoCase(caseId) {
    return mockUndoCase(caseId)
  }

  async function reportIssue(caseId, payload) {
    return mockReportIssue(caseId, payload)
  }

  async function sendToOffice() {
    return mockSendToOffice()
  }

  async function resetStore() {
    return mockResetStore()
  }

  return {
    getCases,
    patchCase,
    cancelCase,
    undoCase,
    reportIssue,
    sendToOffice,
    resetStore
  }
}
