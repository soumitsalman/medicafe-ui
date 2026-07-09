import { DX_OPTIONS, DX_TO_CPT_EYE } from '~/settings/consts'

/** @returns {string[]} */
export function dxOptions() {
  return DX_OPTIONS
}

/**
 * @param {string} dx
 * @returns {{ cpt: string, eye: string }}
 */
export function deriveFromDx(dx) {
  return DX_TO_CPT_EYE[dx] ?? { cpt: '', eye: '' }
}
