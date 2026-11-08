import { describe, expect, it } from 'vitest'
import { shiftMonth, spendingWeeks } from '../../src/lib/purchaseSpending'
import type { Purchase } from '../../src/api/models'
const purchase = (date: string, amount: number) => ({ transaction_date: date, amount_minor: amount }) as Purchase

describe('purchase spending calendar', () => {
  it('clips Monday–Sunday weeks to the month without dropping or double counting edge dates', () => {
    const weeks = spendingWeeks('2026-11', [purchase('2026-11-01', 125), purchase('2026-11-02', 200), purchase('2026-11-30', 450), purchase('2026-12-01', 900)])
    expect(weeks.map(w => w.label)).toEqual(['1–1', '2–8', '9–15', '16–22', '23–29', '30–30'])
    expect(weeks.map(w => w.total)).toEqual([125, 200, 0, 0, 0, 450])
  })
  it('includes leap day and handles year boundaries', () => {
    expect(spendingWeeks('2024-02', [purchase('2024-02-29', 123)]).at(-1)?.total).toBe(123)
    expect(shiftMonth('2026-01', -1)).toBe('2025-12')
    expect(shiftMonth('2026-12', 1)).toBe('2027-01')
  })
})
