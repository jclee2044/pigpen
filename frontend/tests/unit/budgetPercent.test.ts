import {describe,it,expect} from 'vitest'
import {amountToPercent,percentToAmount} from '../../src/lib/budgetPercent'

describe('budget allocation conversions',()=>{
 it('converts both directions, including over-budget values and cent rounding',()=>{
  expect(amountToPercent(100001,300000)).toBe('33.33')
  expect(percentToAmount('25',300000)).toBe(75000)
  expect(percentToAmount('125.00',600000)).toBe(750000)
  expect(percentToAmount('0.50',100)).toBe(1)
  expect(amountToPercent(1,32)).toBe('3.13')
  expect(amountToPercent(10000,0)).toBe('0.00')
 })
 it('keeps large supported amounts exact in both directions',()=>{
  expect(amountToPercent(9000000000000,9000000000000)).toBe('100.00')
  expect(percentToAmount('33.33',9000000000000)).toBe(2999700000000)
 })
})
