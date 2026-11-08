// Integer arithmetic keeps repeated tab switches from changing exact cents.
export function amountToPercent(amountMinor: number, incomeMinor: number): string {
 if (!incomeMinor) return '0.00'
 const income=BigInt(incomeMinor)
 const basisPoints=(BigInt(amountMinor)*10000n+income/2n)/income
 return `${basisPoints/100n}.${String(basisPoints%100n).padStart(2,'0')}`
}
export function percentToAmount(percent: string, incomeMinor: number): number {
 const [whole='',fraction='']=percent.split('.')
 const basisPoints=BigInt(whole||'0')*100n+BigInt(fraction.padEnd(2,'0')||'0')
 return Number((basisPoints*BigInt(incomeMinor)+5000n)/10000n)
}
