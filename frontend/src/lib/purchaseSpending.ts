import type { Purchase } from '../api/models'

/** Calendar weeks start Monday; edge weeks contain only this month's dates. */
export function spendingWeeks(month: string, purchases: Purchase[]) {
  const first = new Date(`${month}-01T12:00:00Z`)
  const last = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 0)).getUTCDate()
  const firstEnd = Math.min(last, 7 - (first.getUTCDay() + 6) % 7)
  const weeks = []
  for (let start = 1; start <= last;) {
    const end = start === 1 ? firstEnd : Math.min(last, start + 6)
    const date = (day: number) => `${month}-${String(day).padStart(2, '0')}`
    const items = purchases.filter(p => p.transaction_date >= date(start) && p.transaction_date <= date(end))
    weeks.push({ start: date(start), end: date(end), label: `${start}–${end}`, items,
      total: items.reduce((sum, p) => sum + p.amount_minor, 0) })
    start = end + 1
  }
  return weeks
}
export function shiftMonth(month: string, direction: number) {
  const [year = 0, number = 1] = month.split('-').map(Number)
  const index = year * 12 + number - 1 + direction
  return `${String(Math.floor(index / 12)).padStart(4, '0')}-${String(index % 12 + 1).padStart(2, '0')}`
}
