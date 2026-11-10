"""Synthetic smoke benchmark; not a substitute for real receipt acceptance."""
from pathlib import Path
import json,subprocess,time,resource,sys
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageFilter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from pigpen.receipt_parser import parse_receipt
out=ROOT/'output/receipt-scan/benchmark';out.mkdir(parents=True,exist_ok=True)
font_path='/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf'
results=[]
for i in range(30):
    font=ImageFont.truetype(font_path,24+i%4*2)
    im=Image.new('RGB',(760,900),(245,243,235));d=ImageDraw.Draw(im)
    a=125+i*37;b=399+i*11;tax=(a+b)*6//100;total=a+b+tax
    lines=['PIGPEN MARKET',f'2026-11-{i%28+1:02}',f'Apples        {a/100:.2f}',f'Bread         {b/100:.2f}',f'Subtotal      {(a+b)/100:.2f}',f'Tax           {tax/100:.2f}',f'{"GRAND TOTAL" if i%2 else "TOTAL"}   {total/100:.2f}','Cash         50.00',f'Change        {(5000-total)/100:.2f}']
    for j,line in enumerate(lines):d.text((35,35+j*75),line,font=font,fill=(30,30,30))
    im=im.rotate([-3,0,2][i%3],fillcolor='white')
    if i%5==0:im=im.filter(ImageFilter.GaussianBlur(.5))
    path=out/f'{i:02}.png';im.save(path)
    start=time.monotonic()
    p=subprocess.run([str(ROOT/'backend/.ocr-venv/bin/python'),str(ROOT/'tools/receipt_ocr.py'),str(path)],capture_output=True,text=True,timeout=45)
    parsed=parse_receipt(json.loads(p.stdout)) if not p.returncode else {}
    results.append({'case':i,'expected':total,'actual':parsed.get('amount_minor'),'items':len(parsed.get('line_items',[])),'seconds':round(time.monotonic()-start,3)})
summary={'synthetic_only':True,'cases':len(results),'exact_totals':sum(r['actual']==r['expected'] for r in results),'abstained':sum(r['actual'] is None for r in results),'incorrect_totals':sum(r['actual'] is not None and r['actual']!=r['expected'] for r in results),'p95_process_seconds':sorted(r['seconds'] for r in results)[28],'peak_child_rss_KiB':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'results':results}
(out/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='results'}))
