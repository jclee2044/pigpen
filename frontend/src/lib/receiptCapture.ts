/** Local text-on-paper analysis. Preview frames never leave the device. */
export interface ReceiptFrame {gray:Uint8Array; width:number; bounds:number[]; sharp:boolean}
/** Match preview and saved photo; 1× always preserves the complete camera frame. */
export function receiptCrop(width:number,height:number,zoom=1){
 const scale=Math.max(1,Math.min(4,zoom)),w=width/scale,h=height/scale
 return {x:(width-w)/2,y:(height-h)/2,width:w,height:h}
}
export function receiptPreviewSize(width:number,height:number){
 const scale=Math.min(1,480/Math.max(width,height))
 return {width:Math.max(1,Math.round(width*scale)),height:Math.max(1,Math.round(height*scale))}
}
interface Ink {left:number;right:number;top:number;bottom:number;pixels:number;edge:number}
export function inspectReceipt(data:Uint8ClampedArray,width:number,height:number):ReceiptFrame|null{
 const n=width*height,gray=new Uint8Array(n),ink=new Uint8Array(n),stride=width+1
 const sums=new Uint32Array(stride*(height+1)),colors=new Uint32Array(sums.length)
 for(let y=0;y<height;y++){
  let sum=0,color=0
  for(let x=0;x<width;x++){
   const p=y*width+x,r=data[p*4]!,g=data[p*4+1]!,b=data[p*4+2]!,max=Math.max(r,g,b)
   gray[p]=Math.round((r+g+b)/3);sum+=gray[p]!
   color+=max?Math.round((max-Math.min(r,g,b))/max*255):0
   sums[(y+1)*stride+x+1]=sums[y*stride+x+1]!+sum
   colors[(y+1)*stride+x+1]=colors[y*stride+x+1]!+color
  }
 }
 const radius=Math.max(5,Math.round(width/30))
 const average=(table:Uint32Array,x0:number,y0:number,x1:number,y1:number)=>(table[y1*stride+x1]!-table[y0*stride+x1]!-table[y1*stride+x0]!+table[y0*stride+x0]!)/((x1-x0)*(y1-y0))
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const x0=Math.max(0,x-radius),x1=Math.min(width,x+radius+1),y0=Math.max(0,y-radius),y1=Math.min(height,y+radius+1)
  const mean=average(sums,x0,y0,x1,y1),color=average(colors,x0,y0,x1,y1)
  if(mean>90&&color<100&&gray[y*width+x]!<mean-Math.max(18,mean*.12))ink[y*width+x]=1
 }
 const queue=new Int32Array(n),letters:Ink[]=[]
 for(let i=0;i<n;i++){
  if(!ink[i])continue
  let head=0,tail=1,left=width,right=0,top=height,bottom=0,edge=0
  queue[0]=i;ink[i]=0
  while(head<tail){
   const p=queue[head++]!,x=p%width,y=Math.floor(p/width),v=gray[p]!
   left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y)
   let gradient=0
   for(const next of [x>0?p-1:-1,x<width-1?p+1:-1,p-width,p+width]){
    if(next<0||next>=n)continue
    gradient=Math.max(gradient,Math.abs(v-gray[next]!))
    if(ink[next]){ink[next]=0;queue[tail++]=next}
   }
   edge+=gradient
  }
  const w=right-left+1,h=bottom-top+1
  if(tail>=2&&h>=2&&h<height*.065&&w<width*.12&&w/h<8&&tail/(w*h)>.08)
   letters.push({left,right,top,bottom,pixels:tail,edge:edge/tail})
 }
 if(letters.length<25||letters.length>1500)return null
 // Ignore isolated flecks, but never automatically capture visible text cut
 // by the frame. A paper edge itself is allowed to meet the frame.
 const heights=letters.map(l=>l.bottom-l.top+1).sort((a,b)=>a-b),typical=heights[Math.floor(heights.length/2)]!
 const useful=letters.filter(l=>l.bottom-l.top+1>=typical*.5&&letters.filter(other=>other!==l&&Math.abs((other.top+other.bottom-l.top-l.bottom)/2)<typical*.8&&Math.abs((other.left+other.right-l.left-l.right)/2)<typical*10).length>=2)
 if(useful.length<25)return null
 if(useful.some(l=>(l.left<2||l.right>width-3||l.top<2||l.bottom>height-3)&&l.pixels>=5&&l.edge>35))return null
 const left=Math.min(...useful.map(l=>l.left)),right=Math.max(...useful.map(l=>l.right))
 const top=Math.min(...useful.map(l=>l.top)),bottom=Math.max(...useful.map(l=>l.bottom))
 const w=right-left+1,h=bottom-top+1
 if(w<width*.25||h<height*.25||w/h<.2||w/h>2)return null
 let lines=0
 for(let s=0;s<4;s++){
  const column=useful.filter(l=>((l.left+l.right)/2-left)/w>=s/4&&((l.left+l.right)/2-left)/w<(s+1)/4).sort((a,b)=>(a.top+a.bottom)-(b.top+b.bottom))
  let last=-height,count=0,rows=0
  for(const letter of column){
   const y=(letter.top+letter.bottom)/2
   if(y-last>typical*.8){if(count>=3)rows++;last=y;count=1}else count++
  }
  if(count>=3)rows++
  lines=Math.max(lines,rows)
 }
 if(lines<5)return null
 // Measure edges on actual letter strokes, not on the paper silhouette or
 // empty background. This avoids calling low-resolution preview text blurry
 // merely because most of the frame contains blank paper.
 const edges=useful.map(l=>l.edge).sort((a,b)=>a-b),detail=edges[Math.floor(edges.length*.5)]!
 return {gray,width,bounds:[left,top,right,bottom],sharp:detail>35}
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
  const scale=Math.max(frame.width,frame.gray.length/frame.width)/320
  if(frame.bounds.some((v,i)=>Math.abs(v-old.bounds[i]!)>8*scale||Math.abs(v-this.anchor[i]!)>14*scale))return restart()
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
