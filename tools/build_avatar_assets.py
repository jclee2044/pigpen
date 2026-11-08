"""Build original, aligned SVG avatar layers using only Python's standard library."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / 'assets/avatars/pig-v1'
INK = '#71363c'
def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><g stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>\n'
def path(d, fill='none', extra=''):
    return f'<path d="{d}" fill="{fill}" {extra}/>'
def ellipse(x,y,rx,ry,fill,extra=''):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" {extra}/>'
def write(group, key, body):
    p=ROOT/group/f'{key}.svg'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(svg(body))
    return {'id':key,'label':key.replace('-',' ').title(),'file':f'{group}/{key}.svg'}

# Portrait designed around fixed eye, neck and crown anchors; all layers share the canvas.
base = path('M151 384 C91 405 81 360 105 352 C125 345 137 371 115 374', '#f49bab')
base += path('M176 306 C145 340 139 403 159 447 Q185 475 256 470 Q330 476 353 447 C375 403 355 341 333 306 Z','#f7a9b8')
base += ellipse(164,429,35,39,'#ef8fa2')+ellipse(348,429,35,39,'#ef8fa2')
base += path('M205 379 L208 450 Q212 478 240 468 L249 390 M307 379 L304 450 Q300 478 272 468 L263 390','#f7a9b8')
base += path('M208 448 Q224 441 240 450 L240 468 Q218 476 208 458 M272 450 Q288 441 304 448 L304 458 Q294 476 272 468','#d96f87')
base += path('M151 179 C113 156 115 105 147 94 Q177 84 207 118 M306 115 Q335 66 361 94 C384 121 370 160 353 180','#f7a9b8')
base += path('M147 139 Q139 109 161 112 L187 131 Z M327 128 Q348 98 356 117 L353 145 Z','#ef7e96','stroke="none"')
base += path('M123 229 C120 159 173 120 247 118 C325 111 385 157 389 227 C393 295 337 330 259 332 C182 335 126 304 123 229 Z','#ffb4c3')
base += path('M218 138 Q249 128 279 132','none','stroke-width="12"')
base += path('M218 135 Q248 126 279 129','none','stroke="#a45362" stroke-width="4"')
base += ellipse(164,257,22,15,'#f68ca3','stroke="none"')+ellipse(348,257,22,15,'#f68ca3','stroke="none"')
base += path('M158 253 L154 261 M170 253 L166 261 M342 253 L338 261 M354 253 L350 261','none','stroke="#e56683" stroke-width="3"')
base += path('M191 199 Q202 189 214 195 M298 195 Q310 188 321 199','none','stroke-width="5"')
base += ellipse(205,224,11,14,'#41272b','stroke="none"')+ellipse(307,224,11,14,'#41272b','stroke="none"')
base += ellipse(208,219,3.5,4,'#fff','stroke="none"')+ellipse(310,219,3.5,4,'#fff','stroke="none"')
base += ellipse(256,253,38,27,'#f48da3','stroke-width="5"')
base += ellipse(242,253,5,9,'#9b475a','stroke="none"')+ellipse(270,253,5,9,'#9b475a','stroke="none"')
base += path('M239 293 Q257 309 277 290','none','stroke-width="5"')
base += path('M161 171 L169 163 M181 153 L185 150','none','stroke="#ffe2e8" stroke-width="9"')
manifest={'version':1,'viewBox':[0,0,512,512],'layerOrder':['background','base','bandana','eyelashes','glasses','hat'],'base':write('base','pig',base),'groups':{}}
palettes={'background':{'cream':'#fff1d8','sage':'#cadfc9','sky':'#c7e5f4','lilac':'#ddd1ef','peach':'#f8d3bd','rose':'#f4cbd7','butter':'#f6e59e','slate':'#8192aa'},'bandana':{'grass':'#49852e','teal':'#248b88','blue':'#407bb7','purple':'#865aa7','coral':'#d65b62','gold':'#dca53c','rose':'#bd5e8b','charcoal':'#4e5665'}}
for group, colors in palettes.items():
    items=[]
    if group=='bandana': items.append({'id':'none','label':'No bandana','file':None})
    for key,color in colors.items():
        if group=='background': body=f'<path d="M0 0H512V512H0Z" fill="{color}" stroke="none"/>'
        else:
            body=path('M174 325 Q131 300 119 320 Q130 348 166 341 Q131 343 125 367 Q154 376 179 345',color)
            body+=path('M174 323 Q256 354 338 323 Q325 367 256 397 Q208 373 174 323 Z',color)
            body+=path('M187 336 Q255 375 324 338 Q258 359 187 336','#000','opacity=".14" stroke="none"')
            body+=ellipse(173,337,12,14,color)
            body+=path('M239 374 L256 382 L273 374','none','stroke="#fff" opacity=".55" stroke-width="3"')
        item=write(group,key,body); item['color']=color; items.append(item)
    manifest['groups'][group]=items
hats={
'beanie':path('M175 141 Q174 66 256 65 Q334 65 337 141 Z','#dfaa46')+path('M173 126 Q254 110 339 126 L338 151 Q256 137 174 151 Z','#efc56d')+ellipse(256,61,17,14,'#efc56d')+path('M204 117 Q203 92 219 80 M237 111 L239 78 M271 111 L269 78 M307 117 Q308 92 292 80','none','stroke="#b98131" stroke-width="4"'),
'baseball-cap':path('M171 136 Q182 63 263 74 Q318 79 337 140 Z','#397f88')+path('M163 137 Q246 117 340 135 Q368 140 376 154 Q288 171 163 150 Z','#67aeb4')+path('M257 77 Q277 97 276 126','none','stroke="#235b65" stroke-width="4"')+ellipse(259,73,9,5,'#235b65'),
'bucket-hat':path('M185 83 Q256 68 327 83 L340 140 L172 140 Z','#e7c89a')+path('M171 128 Q255 148 341 128 L365 164 Q255 190 147 164 Z','#f4dcb8')+path('M183 116 Q257 134 330 116','none','stroke="#b69066" stroke-width="4"'),
'party-hat':path('M188 139 L256 35 L324 139 Q257 163 188 139 Z','#9b78c4')+path('M220 90 L295 103 L307 123 L210 106 Z','#f4ce67','stroke="none"')+ellipse(256,34,12,12,'#f4ce67')+ellipse(249,124,6,6,'#fff1d8','stroke="none"'),
'crown':path('M182 101 L216 121 L256 80 L296 121 L330 101 L316 154 Q256 143 196 154 Z','#e9b844')+path('M198 142 Q256 132 314 142','none','stroke="#ffdf79" stroke-width="6"')+ellipse(256,124,7,9,'#e16d85','stroke-width="3"'),
'beret':path('M168 125 Q140 79 212 69 Q290 47 337 87 Q369 118 320 140 L189 144 Z','#b95c77')+path('M187 132 Q253 117 325 132 L321 151 Q255 138 191 151 Z','#89415c')+path('M255 66 Q252 52 263 48','none','stroke="#89415c" stroke-width="10"')}
manifest['groups']['hat']=[{'id':'none','label':'No hat','file':None}]+[write('hat',k,v) for k,v in hats.items()]
glasses={}
for name in ['round','square','sunglasses','cat-eye','monocle','rounded','aviator','browline']:
    b=''
    if name=='monocle':
        b=ellipse(307,226,27,27,'none','stroke="#a77d37" stroke-width="5"')+path('M331 239 Q358 287 328 315','none','stroke="#a77d37" stroke-width="3"')
    else:
        color='#49343f' if name in ['round','sunglasses'] else ('#a54465' if name=='cat-eye' else '#222222')
        b=path('M175 222 L157 212 M337 222 L355 212 M233 223 Q256 213 279 223','none',f'stroke="{color}" stroke-width="6"')
        for x in [205,307]:
            if name=='round': b+=ellipse(x,226,28,28,'none',f'stroke="{color}" stroke-width="6"')
            elif name=='rounded':
                b+=path(f'M{x-33} 211 Q{x} 199 {x+33} 211 L{x+29} 237 Q{x+24} 256 {x} 256 Q{x-24} 256 {x-29} 237 Z','none',f'stroke="{color}" stroke-width="6"')
                b+=path(f'M{x-29} 213 L{x-25} 213','none','stroke="#d4c6a7" stroke-width="2"')
            elif name=='aviator': b+=path(f'M{x-29} 213 Q{x} 202 {x+29} 213 L{x+27} 236 Q{x+21} 258 {x} 250 Q{x-31} 244 {x-29} 213 Z','none',f'stroke="{color}" stroke-width="4"')
            elif name=='browline':
                b+=ellipse(x,228,29,25,'none',f'stroke="{color}" stroke-width="3"')
                b+=path(f'M{x-29} 218 Q{x} 201 {x+29} 218','none',f'stroke="{color}" stroke-width="9"')
            elif name=='cat-eye': b+=path(f'M{x-32} 209 L{x+29} 214 Q{x+32} 248 {x} 248 Q{x-25} 248 {x-32} 209 Z','none',f'stroke="{color}" stroke-width="6"')
            else:
                b+=f'<rect x="{x-29}" y="207" width="58" height="40" rx="12" fill="{"#343642" if name=="sunglasses" else "none"}" stroke="{color}" stroke-width="6"/>'
                if name=='sunglasses': b+=path(f'M{x-15} 220 L{x+2} 216','none','stroke="#8eabb6" stroke-width="4"')
    glasses[name]=b
# Keep original IDs and artwork; new colors use explicit manifest IDs.
frame_colors={'original':None,'black':'#222222','tortoiseshell':'url(#tortoise)','brown':'#75452f','gold':'#b88935','rose':'#b64d73','blue':'#376ba1','teal':'#247e7b','purple':'#7952a1'}
pattern='<defs><pattern id="tortoise" patternUnits="userSpaceOnUse" width="29" height="23"><rect width="29" height="23" fill="#30231d" stroke="none"/><path d="M2 2L10 0L14 7L6 12Z M21 15L29 12L29 22L23 23Z" fill="#b65d23" stroke="none"/><path d="M5 4L9 3L10 7L7 9Z M24 17L28 16L28 20L25 21Z" fill="#e6aa52" stroke="none"/></pattern></defs>'
manifest['groups']['glasses']=[{'id':'none','label':'No glasses','file':None,'shape':'none','frameColor':'original'}]
for shape,body in glasses.items():
    for shade,color in frame_colors.items():
        artwork=body
        if color:
            for old in ['#49343f','#a54465','#222222','#a77d37']:
                artwork=artwork.replace(f'stroke="{old}"',f'stroke="{color}"')
        if shade=='tortoiseshell': artwork=pattern+artwork
        identifier=shape if shade=='original' else f'{shape}-{shade}'
        item=write('glasses',identifier,artwork)
        item.update(shape=shape,frameColor=shade,label=shape.replace('-',' ').title()+('' if shade=='original' else ' · '+shade.title()))
        manifest['groups']['glasses'].append(item)
# Lashes belong to the eyes and sit behind eyewear; opaque sunglasses hide them.
lashes = path('M197 215 Q189 214 186 208 M195 221 Q186 221 182 216 M196 227 Q187 230 183 226 M315 215 Q323 214 326 208 M317 221 Q326 221 330 216 M316 227 Q325 230 329 226', 'none', 'stroke="#41272b" stroke-width="4"')
manifest['groups']['eyelashes']=[{'id':'none','label':'No eyelashes','file':None}, {**write('eyelashes','classic',lashes),'label':'Eyelashes'}]
manifest['default']={'background':'cream','bandana':'grass','glasses':'none','hat':'none','eyelashes':'none'}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Self-contained preview: inline the assets to work directly from file:// without fetching.
assets={str(p.relative_to(ROOT)):p.read_text() for p in ROOT.glob('*/*.svg')}
data=json.dumps({'manifest':manifest,'assets':assets})
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PigPen avatar studio</title>
<style>*{box-sizing:border-box}body{margin:0;background:#faf6f0;color:#49343f;font:16px system-ui,sans-serif}main{max-width:1080px;margin:50px auto;padding:24px}.eyebrow{font-size:12px;letter-spacing:3px;text-transform:uppercase;color:#8c5d68}h1{font-size:44px;letter-spacing:-2px;margin:12px 0}p{color:#806a71;line-height:1.6}.studio{display:grid;grid-template-columns:1fr 1fr;gap:48px;margin-top:32px}#avatar{width:100%;border-radius:32px;overflow:hidden;line-height:0}fieldset{border:0;padding:0;margin:0 0 24px}legend{font-weight:700;margin-bottom:10px}button{font:inherit;cursor:pointer;border:1px solid #d8c7cb;background:white;color:#49343f;border-radius:12px;padding:10px 13px;margin:0 7px 7px 0}button[aria-pressed=true]{background:#49343f;color:white;border-color:#49343f}button:focus-visible{outline:3px solid #397f88;outline-offset:3px}.swatch{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:7px;border:1px solid #0002}#download{background:#397f88;color:white;border:0;padding:14px 22px}small{color:#806a71} @media(max-width:700px){main{margin:10px auto}.studio{grid-template-columns:1fr;gap:24px}#avatar{max-width:420px;margin:auto}h1{font-size:36px}}</style>
<main><div class="eyebrow">PigPen / Avatar collection 01</div><h1>A little pig. All you.</h1><p>Pick a hat, change your colors, find your look.</p><div class="studio"><section><div id="avatar" role="img" aria-label="Customized pig avatar"></div><p><button id="download">Download SVG</button></p><small>Scalable artwork · 512 × 512 · Every layer interchangeable</small></section><section id="controls" aria-label="Avatar options"></section></div></main><script>
const DATA=__DATA__; const {manifest,assets}=DATA; const selected={...manifest.default};
function content(file){return file?assets[file].replace(/^.*?<svg[^>]*>/s,'').replace(/<\\/svg>\\s*$/,''):''}
function composite(){return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" style="width:100%;height:auto">'+manifest.layerOrder.map(g=>content(g==='base'?manifest.base.file:manifest.groups[g].find(v=>v.id===selected[g]).file)).join('')+'</svg>'}
function render(){document.querySelector('#avatar').innerHTML=composite();document.querySelector('#avatar').setAttribute('aria-label',`Pig avatar: ${Object.values(selected).join(', ')}`);document.querySelectorAll('[data-group]').forEach(b=>b.setAttribute('aria-pressed',String(selected[b.dataset.group]===b.dataset.id)))}
for(const group of ['background','hat','bandana','glasses','eyelashes']){const field=document.createElement('fieldset');const title=document.createElement('legend');title.textContent=group[0].toUpperCase()+group.slice(1);field.append(title);for(const item of manifest.groups[group]){const b=document.createElement('button');b.type='button';b.dataset.group=group;b.dataset.id=item.id;if(item.color){const s=document.createElement('span');s.className='swatch';s.style.background=item.color;b.append(s)}b.append(document.createTextNode(item.label));b.onclick=()=>{selected[group]=item.id;render()};field.append(b)}document.querySelector('#controls').append(field)}
document.querySelector('#download').onclick=()=>{const url=URL.createObjectURL(new Blob([composite()],{type:'image/svg+xml'}));const a=document.createElement('a');a.href=url;a.download='pigpen-'+Object.values(selected).join('-')+'.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};render();
</script></html>'''
(ROOT/'preview.html').write_text(html.replace('__DATA__',data))
# Representative combinations, including the reference-inspired tortoiseshell frames.
choices=[('cream','none','none','none'),('sage','baseball-cap','grass','round'),('sky','beanie','coral','square'),('lilac','beret','gold','cat-eye'),('peach','bucket-hat','teal','sunglasses'),('butter','party-hat','purple','none'),('rose','crown','blue','monocle'),('slate','none','rose','rounded-tortoiseshell')]
sheet=[]
for i, combo in enumerate(choices):
    selection=dict(zip(['background','hat','bandana','glasses'],combo)); selection['eyelashes']='classic' if i > 0 else 'none'; inner=''
    for group in manifest['layerOrder']:
        file=manifest['base']['file'] if group=='base' else next(x['file'] for x in manifest['groups'][group] if x['id']==selection[group])
        if file: inner+=assets[file].split('>',1)[1].rsplit('</svg>',1)[0]
    sheet.append(f'<svg x="{(i%4)*256}" y="{(i//4)*256}" width="256" height="256" viewBox="0 0 512 512">{inner}</svg>')
(ROOT/'contact-sheet.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="512">'+''.join(sheet)+'</svg>')
from math import prod
print(f'Built {len(assets)} layers; {prod(len(v) for v in manifest["groups"].values()):,} combinations; preview and contact sheet.')
