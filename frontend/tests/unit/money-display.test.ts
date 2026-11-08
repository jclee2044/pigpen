import { afterEach, expect, test } from 'vitest'
import { appearance } from '../../src/state/appearance'
import { money, inputMoney, parseMoney } from '../../src/lib/money'

afterEach(()=>{appearance.showCents=true})
test('display preference rounds currency without changing editable or saved cents',()=>{
 expect(money(123450)).toBe('$1,234.50')
 appearance.showCents=false
 for(const [amount,display] of [[123449,'$1,234'],[123450,'$1,235'],[-123450,'-$1,235'],[0,'$0']] as const)expect(money(amount)).toBe(display)
 expect(inputMoney(123450)).toBe('1234.50')
 expect(parseMoney('1234.50')).toBe(123450)
 appearance.showCents=true
 expect(money(123450)).toBe('$1,234.50')
})
