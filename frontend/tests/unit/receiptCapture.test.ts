import {describe,it,expect} from 'vitest'
import {inspectReceipt,SteadyReceipt,receiptCrop,receiptPreviewSize} from '../../src/lib/receiptCapture'
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
function unevenPicture(text=true,curved=false){
 const pixels=picture(false)
 for(let y=25;y<295;y++)for(let x=40;x<200;x++){
  const bend=curved?Math.round(22*Math.sin((x-40)/160*Math.PI)):0
  const lineY=y-bend
  const ink=text&&x>=55&&x<180&&lineY>=55&&lineY<250&&lineY%18<3&&x%7<4
  // A broad crease shadow crosses the entire receipt, splitting the old
  // fixed-brightness paper mask into two undersized components.
  const shade=1-.52*Math.exp(-(((y-160)/38)**2))
  const value=Math.round((ink?30:240)*shade)
  const p=(y*240+x)*4;pixels[p]=pixels[p+1]=pixels[p+2]=value
 }
 return pixels
}
function blur(pixels:Uint8ClampedArray){
 const result=new Uint8ClampedArray(pixels)
 for(let y=4;y<316;y++)for(let x=4;x<236;x++){
  let sum=0
  for(let dy=-4;dy<=4;dy++)for(let dx=-4;dx<=4;dx++)sum+=pixels[((y+dy)*240+x+dx)*4]!
  const p=(y*240+x)*4;result[p]=result[p+1]=result[p+2]=Math.round(sum/81)
 }
 return result
}
describe('receipt automatic capture',()=>{
 it.each([false,true])('recognizes shaded paper with curved text: %s',curved=>{
  const frame=inspectReceipt(unevenPicture(true,curved),240,320)
  expect(frame?.sharp).toBe(true)
  const steady=new SteadyReceipt()
  for(const time of [0,250,500])expect(steady.update(frame,time)).toBe(false)
  expect(steady.update(frame,750)).toBe(true)
 })
 it('does not mistake folds on blank paper for receipt text',()=>{
  expect(inspectReceipt(unevenPicture(false),240,320)).toBeNull()
 })
 it('rejects actual blur, cropped text and repeated shadows without text',()=>{
  for(const pixels of [picture(),unevenPicture(true,true)])
   expect(inspectReceipt(blur(pixels),240,320)?.sharp??false).toBe(false)
  expect(inspectReceipt(picture(true,70),240,320)===null).toBe(true)
  const shadows=picture(false)
  for(let y=25;y<295;y++)for(let x=40;x<200;x++){
   const p=(y*240+x)*4,value=190+50*Math.sin(y/6)
   shadows[p]=shadows[p+1]=shadows[p+2]=value
  }
  expect(inspectReceipt(shadows,240,320)?.sharp??false).toBe(false)
 })
 it('handles bowed paper edges without treating surrounding background as ink',()=>{
  const pixels=unevenPicture(true,true)
  for(let y=25;y<295;y++){
   const inset=Math.round(18*Math.sin((y-25)/270*Math.PI))
   for(let x=40;x<200;x++)if(x<40+inset||x>=200-inset){
    const p=(y*240+x)*4;pixels[p]=pixels[p+1]=pixels[p+2]=35
   }
  }
  expect(inspectReceipt(pixels,240,320)?.sharp).toBe(true)
 })
 it('still recognizes paper against a lighter neutral surface',()=>{
  const pixels=picture()
  for(let y=0;y<320;y++)for(let x=0;x<240;x++)if(x<40||x>=200||y<25||y>=295){
   const p=(y*240+x)*4;pixels[p]=pixels[p+1]=pixels[p+2]=130
  }
  expect(inspectReceipt(pixels,240,320)?.sharp).toBe(true)
 })
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

describe('receipt camera framing',()=>{
 it('preserves all source pixels at 1x regardless of source aspect ratio',()=>{
  for(const [width,height] of [[258,258],[1920,1080],[750,1000]]){
   expect(receiptCrop(width!,height!)).toEqual({x:0,y:0,width,height})
   const size=receiptPreviewSize(width!,height!)
   expect(size.width/size.height).toBeCloseTo(width!/height!,2)
   expect(Math.max(size.width,size.height)).toBeLessThanOrEqual(480)
  }
 })
 it('keeps zoom centered without adding a portrait crop',()=>{
  expect(receiptCrop(1920,1080,2)).toEqual({x:480,y:270,width:960,height:540})
 })
 it('allows paper at the frame edge when its text is still fully visible',()=>{
  expect(inspectReceipt(picture(true,40),240,320)?.sharp).toBe(true)
 })
 it('rejects text on a saturated surface',()=>{
  const pixels=picture()
  for(let p=0;p<pixels.length;p+=4)if(pixels[p]===240){pixels[p]=0;pixels[p+1]=240;pixels[p+2]=0}
  expect(inspectReceipt(pixels,240,320)===null).toBe(true)
 })
})
