/**
 * @typedef {'scheduled'|'billable'|'mission'|'cancelled'|'issue'} CaseStatus
 */

/**
 * @typedef {'identity_issue'|'needs_review'} IssueType
 */

/**
 * API-aligned case shape (GET /cases/schedules, POST /cases/billables).
 * @typedef {Object} CaseInfo
 * @property {string} case_id
 * @property {string} [facility_id]
 * @property {string} [provider_id]
 * @property {string} service_date
 * @property {string} [service_time]
 * @property {number} case_pos
 * @property {string} patient_id
 * @property {string} patient_name
 * @property {string} patient_dob
 * @property {string} dx
 * @property {string} cpt
 * @property {string} eye
 * @property {number|null} minutes
 * @property {CaseStatus} status
 * @property {IssueType[]} [sub_status]
 * @property {string} note
 * @property {boolean} mission
 */

/**
 * POST /cases/billables response.
 * @typedef {Object} BillableCasesSubmissionResponse
 * @property {string[]} billable
 * @property {string[]} mission
 * @property {string[]} cancelled
 * @property {string[]} issues
 */

export {}
