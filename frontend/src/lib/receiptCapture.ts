/** Small local preview analysis. No frames leave the device until capture. */
export interface ReceiptFrame {gray:Uint8Array; width:number; bounds:number[]; sharp:boolean}
export function inspectReceipt(data:Uint8ClampedArray,width:number,height:number):ReceiptFrame|null{
 const n=width*height,gray=new Uint8Array(n),paper=new Uint8Array(n)
 for(let i=0;i<n;i++){
  const r=data[i*4]!,g=data[i*4+1]!,b=data[i*4+2]!
  gray[i]=Math.round((r+g+b)/3)
  paper[i]=gray[i]!>145&&Math.max(r,g,b)-Math.min(r,g,b)<65?1:0
 }
 const queue=new Int32Array(n);let best:number[]=[]
 for(let i=0;i<n;i++){
  if(!paper[i])continue
  let head=0,tail=1;queue[0]=i;paper[i]=0
  while(head<tail){
   const p=queue[head++]!,x=p%width
   for(const next of [x>0?p-1:-1,x<width-1?p+1:-1,p-width,p+width]){
    if(next>=0&&next<n&&paper[next]){paper[next]=0;queue[tail++]=next}
   }
  }
  if(tail>best.length)best=Array.from(queue.subarray(0,tail))
 }
 if(best.length<n*.28)return null
 let left=width,right=0,top=height,bottom=0
 for(const p of best){const x=p%width,y=Math.floor(p/width);left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y)}
 const w=right-left+1,h=bottom-top+1
 // Require visible edges so a white wall/screen filling the frame is not captured.
 if(left<3||top<3||right>width-4||bottom>height-4||w/h<.3||w/h>1.1||best.length/(w*h)<.72)return null
 let dark=0,contrast=0,edges=0,rows=0,inRow=false
 for(let y=top+3;y<bottom-3;y++){
  let ink=0
  for(let x=left+3;x<right-3;x++){
   const p=y*width+x,v=gray[p]!
   if(v<115){dark++;ink++}
   const d=Math.abs(v-gray[p+1]!)+Math.abs(v-gray[p+width]!)
   if(d>60){contrast+=d;edges++}
  }
  const textRow=ink>3&&ink<w*.7
  if(textRow&&!inRow)rows++
  inRow=textRow
 }
 if(dark/(w*h)<.006||dark/(w*h)>.25||rows<5)return null
 return {gray,width,bounds:[left,top,right,bottom],sharp:edges>w*h*.025&&contrast/Math.max(edges,1)>110}
}
export class SteadyReceipt{
 private previous:ReceiptFrame|null=null
 private anchor:number[]=[]
 private since=0
 private samples=0
 reset(){this.previous=null;this.anchor=[];this.since=0;this.samples=0}
 update(frame:ReceiptFrame|null,now:number){
  if(!frame?.sharp){this.reset();return false}
  const old=this.previous;this.previous=frame
  const restart=()=>{this.since=now;this.samples=1;this.anchor=[...frame.bounds];return false}
  if(!old||old.width!==frame.width||old.gray.length!==frame.gray.length)return restart()
  if(frame.bounds.some((v,i)=>Math.abs(v-old.bounds[i]!)>8||Math.abs(v-this.anchor[i]!)>14))return restart()
  // Compare the paper after aligning small hand movements; ignore the moving
  // background and compensate for exposure changes rather than requiring
  // nearly identical full-camera frames.
  const dx=Math.round(frame.bounds[0]!-old.bounds[0]!),dy=Math.round(frame.bounds[1]!-old.bounds[1]!)
  const differences:number[]=[]
  for(let y=frame.bounds[1]!+4;y<frame.bounds[3]!-4;y+=2){
   for(let x=frame.bounds[0]!+4;x<frame.bounds[2]!-4;x+=2){
    const ox=x-dx,oy=y-dy
    if(ox>=0&&ox<old.width&&oy>=0&&oy<old.gray.length/old.width)
     differences.push(frame.gray[y*frame.width+x]!-old.gray[oy*old.width+ox]!)
   }
  }
  if(!differences.length)return restart()
  const exposure=differences.reduce((a,b)=>a+b,0)/differences.length
  const motion=differences.reduce((sum,d)=>sum+Math.abs(d-exposure),0)/differences.length
  if(motion>16)return restart()
  this.samples++
  return this.samples>=4&&now-this.since>=700
 }
}
