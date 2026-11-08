import { appearance } from '../state/appearance'

export const MAX_MINOR = 9_000_000_000_000
export function parseMoney(input: string, allowZero = true): number {
  const match = /^(0|[1-9]\d*)(?:\.(\d{1,2}))?$/.exec(input.trim())
  if (!match) throw new Error('Enter an amount such as 12.50, with at most two decimal places.')
  const cents = Number(match[1]) * 100 + Number((match[2] ?? '').padEnd(2,'0'))
  if (!Number.isSafeInteger(cents) || cents > MAX_MINOR || (!allowZero && cents === 0)) throw new Error('Enter an amount within the allowed range' + (allowZero ? '.' : ' greater than zero.'))
  return cents
}
const withCents = new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'})
const withoutCents = new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:0,maximumFractionDigits:0})
export const money = (cents: number) => (appearance.showCents ? withCents : withoutCents).format(cents/100)
export const inputMoney = (cents: number) => `${Math.trunc(cents/100)}.${String(Math.abs(cents%100)).padStart(2,'0')}`
export function today(): string { return new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date()) }
export const monthLabel = (month: string) => new Intl.DateTimeFormat('en-US',{month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(`${month}-15T12:00:00Z`))
