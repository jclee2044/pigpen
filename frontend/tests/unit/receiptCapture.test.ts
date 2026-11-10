import {describe,it,expect} from 'vitest'
import {inspectReceipt,SteadyReceipt} from '../../src/lib/receiptCapture'
function picture(text=true,shift=0){
 const pixels=new Uint8ClampedArray(240*320*4)
 for(let y=0;y<320;y++)for(let x=0;x<240;x++){
  let v=35
  if(x>=40+shift&&x<200+shift&&y>=25&&y<295)v=240
  if(text&&x>=55+shift&&x<180+shift&&y>=55&&y<250&&y%18<3&&(x-shift)%7<4)v=30
  const p=(y*240+x)*4;pixels[p]=pixels[p+1]=pixels[p+2]=v;pixels[p+3]=255
 }
 return pixels
}
describe('receipt automatic capture',()=>{
 it('requires text and sharp edges on visible paper',()=>{
  expect(inspectReceipt(picture(),240,320)?.sharp).toBe(true)
  expect(inspectReceipt(picture(false),240,320)).toBeNull()
  expect(inspectReceipt(new Uint8ClampedArray(240*320*4).fill(240),240,320)).toBeNull()
 })
 it('captures with small hand movement and exposure changes',()=>{
  const steady=new SteadyReceipt()
  for(let i=0;i<5;i++){
   const pixels=picture(true,(i%3)*3)
   for(let p=0;p<pixels.length;p++)if(p%4!==3)pixels[p]=Math.min(255,pixels[p]!+i*2)
   expect(steady.update(inspectReceipt(pixels,240,320),100+i*250)).toBe(i>=3)
  }
 })
 it('resets for large movement, blur, missing paper and explicit cancellation',()=>{
  const steady=new SteadyReceipt(),frame=inspectReceipt(picture(),240,320)!
  for(const time of [0,250,500])expect(steady.update(frame,time)).toBe(false)
  expect(steady.update(inspectReceipt(picture(true,15),240,320),1000)).toBe(false)
  expect(steady.update({...frame,sharp:false},1500)).toBe(false)
  expect(steady.update(frame,2000)).toBe(false)
  expect(steady.update(null,2500)).toBe(false)
  expect(steady.update(frame,3000)).toBe(false)
  steady.reset();expect(steady.update(frame,5000)).toBe(false)
 })
})
