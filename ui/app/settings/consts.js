/**
 * @typedef {{ cpt: string, eye: 'LEFT'|'RIGHT' }} DxDerivation
 */

/** Fixed DX dropdown options (ordered). */
export const DX_OPTIONS = [
  'H25.812',
  'H25.811',
  'H25.10',
  'H25.11',
  'H26.9'
]

/** DX → CPT and eye lookup (mock data). */
/** @type {Record<string, DxDerivation>} */
export const DX_TO_CPT_EYE = {
  'H25.812': { cpt: '00142', eye: 'LEFT' },
  'H25.811': { cpt: '00142', eye: 'RIGHT' },
  'H25.10': { cpt: '00140', eye: 'LEFT' },
  'H25.11': { cpt: '00140', eye: 'RIGHT' },
  'H26.9': { cpt: '00140', eye: 'LEFT' }
}
