/** @param {number|null|undefined} totalMinutes */
export function splitDuration(totalMinutes) {
  if (totalMinutes == null || totalMinutes < 0) {
    return { hours: 0, minutes: 0 }
  }
  return {
    hours: Math.floor(totalMinutes / 60),
    minutes: totalMinutes % 60
  }
}

/** @param {number} hours @param {number} minutes */
export function toTotalMinutes(hours, minutes) {
  return (hours * 60) + minutes
}

/** @param {number} totalMinutes */
export function formatDuration(totalMinutes) {
  if (totalMinutes == null) return '—'
  const { hours, minutes } = splitDuration(totalMinutes)
  if (hours === 0) return `${minutes}m`
  if (minutes === 0) return `${hours}h`
  return `${hours}h ${minutes}m`
}

/**
 * Parse a free-form duration string.
 * Accepts: "1h10m", "1h 10m", "1 hour 10 min", "55 min", "55m", "2 hours".
 * @param {string} text
 */
export function parseDurationText(text) {
  const trimmed = text.trim()
  if (!trimmed) return { hours: 0, minutes: 0 }

  const hourMatch = trimmed.match(/(\d+)\s*(?:h|hr|hour|hours)/i)
  const minMatch = trimmed.match(/(\d+)\s*(?:m|min|mins|minute|minutes)/i)

  if (!hourMatch && !minMatch) return null

  const hours = hourMatch ? Math.max(0, Number(hourMatch[1])) : 0
  const minutes = minMatch ? Math.min(59, Math.max(0, Number(minMatch[1]))) : 0

  return { hours, minutes }
}

/** @param {number} totalMinutes */
export function formatDurationLong(totalMinutes) {
  if (totalMinutes == null) return '—'
  const { hours, minutes } = splitDuration(totalMinutes)
  return `${hours}h ${minutes}m`
}

/** @param {string} iso */
export function formatScheduleTime(iso) {
  return new Date(iso).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}

/** @param {string} iso */
export function formatDisplayDate(iso) {
  return new Date(iso + 'T12:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric'
  })
}

/** @param {Function} fn @param {number} ms */
export function debounce(fn, ms) {
  let timer
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), ms)
  }
}

import { differenceInYears, format, max, parse } from 'date-fns'

/** @param {string} dob YYYY-MM-DD */
export function formatDob(dob) {
  return format(parse(dob, 'yyyy-MM-dd', new Date()), 'MM/dd/yyyy')
}

/**
 * @param {string} dob YYYY-MM-DD
 * @param {string} shiftDate MM-DD-YYYY
 */
export function formatDobWithAge(dob, shiftDate) {
  const birth = parse(dob, 'yyyy-MM-dd', new Date())
  const ref = parse(shiftDate, 'MM-dd-yyyy', new Date())
  const age = differenceInYears(ref, birth)
  return `${format(birth, 'MM/dd/yyyy')} (${age}y)`
}

/** @param {string} shiftDate MM-DD-YYYY */
export function formatShiftDateLong(shiftDate) {
  const d = parse(shiftDate, 'MM-dd-yyyy', new Date())
  return format(d, 'EEEE, MMMM do, yyyy')
}

/** @param {string[]} shiftDates MM-DD-YYYY */
export function formatMaxShiftDate(shiftDates) {
  if (!shiftDates.length) return null
  const parsed = shiftDates.map(d => parse(d, 'MM-dd-yyyy', new Date()))
  return format(max(parsed), 'EEEE, MMMM do, yyyy')
}

/** Simulate network latency for mock API */
export function mockDelay(ms = 200) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/** Deep-clone for returning fresh DTOs */
export function clone(value) {
  return JSON.parse(JSON.stringify(value))
}
