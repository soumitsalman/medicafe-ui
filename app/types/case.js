/**
 * @typedef {'pending'|'completed'|'mission'|'cancelled'|'issue'} CaseStatus
 */

/**
 * @typedef {'identity_issue'|'needs_review'} IssueType
 */

/**
 * @typedef {Object} CaseDto
 * @property {string} id
 * @property {string} date
 * @property {number} pos
 * @property {string} patientId
 * @property {string} name
 * @property {string} dob
 * @property {string} dx
 * @property {string} cpt
 * @property {string} eye
 * @property {number|null} minutes
 * @property {boolean} mission
 * @property {CaseStatus} status
 * @property {IssueType[]} subState
 * @property {string} note
 */

/**
 * @typedef {Object} SendingRowDto
 * @property {string} patient_id
 * @property {Exclude<CaseStatus, 'pending'>} status
 * @property {IssueType[]} [sub_state]
 * @property {number|null} minutes
 * @property {string} dx
 * @property {string} cpt
 * @property {string} eye
 * @property {string} note
 */

/**
 * @typedef {Object} SendingPayloadDto
 * @property {string} date
 * @property {SendingRowDto[]} rows
 */

export {}
