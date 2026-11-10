"""Match OCR text and price rows in reading order, without OCR dependencies."""
import re
from statistics import median

PRICE_TOKEN = re.compile(r'^\s*[$€£]?\s*-?(?:\d[\d,]*)?\.\d{2}\s*(?:-?[A-Z0-9])?\s*$',re.I)


def group_rows(tokens):
    if not tokens:
        return []
    slope=median(t['slope'] for t in tokens if t['width']>20) if any(t['width']>20 for t in tokens) else 0
    def group(pieces):
        rows=[]
        for piece in sorted(pieces,key=lambda p:p['raw_y']-slope*p['center_x']):
            y=piece['raw_y']-slope*piece['center_x']
            target=next((r for r in rows if abs(r['y']-y)<min(r['height'],piece['height'])*.55 and
                         all(piece['x']>=t['x']+t['width'] or t['x']>=piece['x']+piece['width'] for t in r['tokens'])),None)
            if target:target['tokens'].append(piece)
            else:rows.append({'y':y,'raw_y':piece['raw_y'],'height':piece['height'],'tokens':[piece]})
        return rows
    labels=group([t for t in tokens if not PRICE_TOKEN.fullmatch(t['text'])])
    prices=group([t for t in tokens if PRICE_TOKEN.fullmatch(t['text'])])
    # Global, monotonic pairing prevents an early price from stealing the next
    # label and shifting every subsequent amount by one line. Unmatched text
    # (headers/modifiers) and unmatched prices are allowed, never invented.
    n,m=len(labels),len(prices)
    costs=[[float('inf')]*(m+1) for _ in range(n+1)]
    previous={};costs[0][0]=0
    for i in range(n+1):
        for j in range(m+1):
            options=[]
            if i<n:options.append((i+1,j,.65,'label'))
            if j<m:options.append((i,j+1,1.1,'price'))
            if i<n and j<m:
                label,price=labels[i],prices[j]
                h=max(label['height'],price['height'],1)
                distance=abs(label['y']-price['y'])/h if abs(slope)>.08 else abs(label['raw_y']-price['raw_y'])/h
                right=min(t['x'] for t in price['tokens'])>min(t['x'] for t in label['tokens'])
                if right and distance<=1.25:options.append((i+1,j+1,distance,'match'))
            for ni,nj,cost,kind in options:
                if costs[i][j]+cost<costs[ni][nj]:
                    costs[ni][nj]=costs[i][j]+cost;previous[ni,nj]=(i,j,kind)
    matched=set();i,j=n,m
    while i or j:
        pi,pj,kind=previous[i,j]
        if kind=='match':labels[pi]['tokens'].extend(prices[pj]['tokens']);matched.add(pj)
        i,j=pi,pj
    rows=labels+[r for j,r in enumerate(prices) if j not in matched]
    result=[]
    for row in sorted(rows,key=lambda r:r['y']):
        pieces=sorted(row['tokens'],key=lambda p:p['x'])
        result.append({'text':' '.join(p['text'] for p in pieces),'score':min(p['score'] for p in pieces),
                       'tokens':pieces,'y':row['y'],'height':row['height']})
    return result
