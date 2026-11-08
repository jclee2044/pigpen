"""Build standalone SVG/PNG design studies. Standard library + existing rsvg-convert."""
from pathlib import Path
import base64
import html
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BG='#fff8f7'; INK='#382e2d'; MUTED='#827572'; LINE='#eadedb'; PINK='#a94665'; BLUSH='#f6dce4'; SAGE='#e6eddf'; GREEN='#526b4d'; CLAY='#f2dfd2'; BUTTER='#f5edcd'
parts=[]

def rect(x,y,w,h,fill='white',r=16,stroke=None):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')
def text(x,y,s,size=15,color=INK,weight=400,serif=False):
    parts.append(f'<text x="{x}" y="{y}" font-family="{("Liberation Serif" if serif else "DejaVu Sans")}" font-size="{size}" fill="{color}" font-weight="{weight}">{html.escape(str(s))}</text>')
def line(x,y,x2,y2,color=LINE):
    parts.append(f'<path d="M{x} {y}H{x2}" stroke="{color}"/>' if y==y2 else f'<path d="M{x} {y}L{x2} {y2}" stroke="{color}"/>')
def card(x,y,w,h,fill='white'):
    rect(x,y,w,h,fill,18,LINE)
def pill(x,y,label,fill=SAGE,color=GREEN):
    w=len(label)*6.4+24
    rect(x,y,w,27,fill,13)
    text(x+12,y+18,label,11,color,600)
def button(x,y,label,w=150,primary=True):
    rect(x,y,w,42,PINK if primary else 'white',10,None if primary else LINE)
    text(x+16,y+27,label,13,'white' if primary else INK,600)
def icon(x,y,name,color=MUTED,size=22):
    paths={
      'Dashboard':'M3 10L12 3l9 7v11H3Z M9 21v-8h6v8',
      'Purchases':'M5 3h14v19l-3-2-4 2-4-2-3 2Z M8 8h8 M8 12h8 M8 16h5',
      'Budget':'M3 5h18v16H3Z M3 10h18 M16 13v5 M13 15h6',
      'Wish lists':'M12 21S2 15 2 8a5 5 0 0 1 10-2 5 5 0 0 1 10 2c0 7-10 13-10 13Z',
      'Approvals':'M12 2l9 4v6c0 6-9 10-9 10S3 18 3 12V6Z M7 12l3 3 7-7',
      'bell':'M5 17h14l-2-3V9a5 5 0 0 0-10 0v5Z M10 21h4',
      'arrow':'M8 5l7 7-7 7',
      'search':'M18 18l4 4 M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
    }
    parts.append(f'<g transform="translate({x} {y}) scale({size/24})" stroke="{color}" fill="none" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"><path d="{paths[name]}"/></g>')
def pig(x,y,size=40,bg=BLUSH):
    rect(x,y,size,size,bg,size/2)
    asset=ROOT/'assets/avatars/pig-v1/base/pig.svg'
    data=base64.b64encode(asset.read_bytes()).decode()
    parts.append(f'<image x="{x}" y="{y}" width="{size}" height="{size}" href="data:image/svg+xml;base64,{data}"/>')
def progress(x,y,w,p,fill=PINK):
    rect(x,y,w,7,'#f0e7e3',3)
    rect(x,y,max(2,w*p),7,fill,3)

def shell(screen,mobile=False):
    global parts
    parts=[]
    w,h=(390,1040) if mobile else (1440,1040)
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    rect(0,0,w,h,BG,0)
    if mobile:
        text(22,27,'9:41',12,INK,600); text(302,27,'▰  ▰  ▰',11,INK)
        text(20,77,'pigpen',29,PINK,700,True)
        icon(284,53,'bell',INK); rect(301,52,7,7,PINK,4); pig(326,47,38)
        line(0,97,390,97)
    else:
        rect(0,0,1440,80,'white',0); line(0,80,1440,80)
        text(34,51,'pigpen',36,PINK,700,True)
        text(264,46,'A little planning. More room to live.',13,MUTED)
        icon(1160,27,'bell',INK); rect(1177,25,8,8,PINK,4)
        line(1203,21,1203,60)
        pig(1224,19,42); text(1280,36,'Alex',14,INK,600); text(1280,55,'Our household  ⌄',11,MUTED)
        rect(0,81,224,959,'white',0); line(224,81,224,1040)
        text(26,123,'OUR HOUSEHOLD',10,MUTED,600)
        for i,n in enumerate(['Dashboard','Purchases','Budget','Wish lists','Approvals']):
            y=145+i*58
            if n==screen: rect(14,y,195,46,BLUSH,10)
            icon(27,y+12,n,PINK if n==screen else MUTED)
            text(64,y+30,n,14,PINK if n==screen else MUTED,600 if n==screen else 400)
        card(17,835,190,104,BG)
        text(31,863,'Small steps, together.',14,INK,600,True)
        text(31,887,'A home for your',11,MUTED); text(31,905,'household plans.',11,MUTED)
        text(28,984,'Profiles & settings',12,MUTED)
        text(28,1011,'Synced just now',10,GREEN)
    return w,h

def finish(screen,mobile):
    if mobile:
        rect(0,957,390,83,'white',0); line(0,957,390,957)
        for i,n in enumerate(['Dashboard','Purchases','Budget','Wish lists','Approvals']):
            cx=39+i*78
            if n==('Dashboard' if screen=='Notifications' else screen): rect(cx-23,965,46,29,BLUSH,14)
            icon(cx-11,969,n,PINK if n==('Dashboard' if screen=='Notifications' else screen) else MUTED,22)
            short={'Dashboard':'Dashboard','Purchases':'Purchases','Budget':'Budget','Wish lists':'Wish lists','Approvals':'Approvals'}[n]
            # centered labels, all destinations use equal widths
            parts.append(f'<text x="{cx}" y="1013" text-anchor="middle" font-family="DejaVu Sans" font-size="9" fill="{PINK if n==screen else MUTED}">{short}</text>')
        rect(139,1028,112,4,INK,2)
    parts.append('</svg>')
    name=screen.lower().replace(' ','-')+('-mobile' if mobile else '-desktop')
    dest=OUT/f'{name}.svg'; dest.write_text(''.join(parts))
    subprocess.run(['rsvg-convert',str(dest),'-o',str(OUT/f'{name}.png')],check=True)

def title(screen,sub,m=False,action=None):
    x,y=(20,140) if m else (268,141)
    text(x,y,screen,30 if m else 37,INK,500,True)
    text(x,y+28,sub,12 if m else 14,MUTED)
    if action and not m: button(1210,111,action,186)

def purchase_row(x,y,w,name,meta,amount,cat,compact=False):
    rect(x,y,38,38,{'Food':SAGE,'Personal':BLUSH,'Gas':CLAY,'Dates':BUTTER}.get(cat,BLUSH),11)
    text(x+12,y+25,cat[0],14,GREEN if cat=='Food' else PINK,600)
    text(x+52,y+14,name,13,INK,600); text(x+52,y+34,meta,10,MUTED)
    text(x+w-73,y+15,amount,14,INK,600)
    if not compact: text(x+w-73,y+35,cat,10,MUTED)

def dashboard(m):
    shell('Dashboard',m)
    if m:
        title('Good morning, Alex','Here’s your household at a glance.',True)
        pill(20,190,'November 2026',fill='white',color=INK)
        card(20,235,350,158,BLUSH)
        text(38,265,'LEFT IN THIS MONTH’S PLAN',10,PINK,600)
        text(38,313,'$820',43,INK,500,True)
        text(38,341,'$2,360 spent of $3,180 allocated',11,MUTED)
        progress(38,360,314,.742)
        card(20,408,350,100)
        text(38,438,'Your personal allowance',13,INK,600)
        text(38,476,'$150 left',25,INK,500,True); text(202,474,'$50 of $200 spent',10,MUTED)
        button(20,525,'+  Add purchase',350)
        text(20,608,'A little attention',23,INK,500,True)
        card(20,628,350,100,BUTTER)
        text(38,656,'1 request needs your approval',12,INK,600)
        text(38,683,'Living room lamp · Jamie · $85.00',11,MUTED)
        text(38,709,'Review request  →',12,PINK,600)
        text(20,772,'Recent purchases',23,INK,500,True)
        card(20,793,350,144)
        purchase_row(36,811,317,'Weekly groceries','Alex · Today','$86.40','Food',True)
        line(36,863,354,863)
        purchase_row(36,882,317,'Books for the weekend','Alex · Yesterday','$30.00','Personal',True)
    else:
        title('Good morning, Alex','Here’s what’s happening with your household.')
        button(1220,112,'+  Add purchase',176)
        pill(268,195,'November 2026  ⌄',fill='white',color=INK)
        for x,w,label,value,sub,fill in [(268,358,'Allocated','$3,180','Your plan for November','white'),(644,358,'Spent','$2,360','74% of this month’s allocation','white'),(1020,376,'Remaining','$820','Allocated minus recorded spending',BLUSH)]:
            card(x,243,w,156,fill); text(x+24,276,label,13,MUTED,600); text(x+24,326,value,40,INK,500,True); text(x+24,362,sub,11,MUTED)
        text(268,449,'Your month, together',25,INK,500,True)
        card(268,472,718,203)
        text(292,507,'Household budget',16,INK,600); text(831,506,'View budget →',12,PINK,600)
        progress(292,535,666,.742)
        for x,label,val in [(292,'Food','$313 left'),(521,'Dates','$140 left'),(747,'Personal · Alex','$150 left')]:
            text(x,581,label,12,MUTED); text(x,613,val,23,INK,500,True)
        text(292,650,'November 1–30 · Recorded purchases only',10,MUTED)
        card(1006,472,390,203,BUTTER)
        text(1030,509,'A little attention',23,INK,500,True)
        text(1030,544,'1 request needs your approval',13,INK,600)
        text(1030,573,'Jamie · Living room lamp · $85.00',12,MUTED)
        button(1030,602,'Review request',160,False)
        text(268,727,'Recent purchases',25,INK,500,True); text(1286,725,'View all →',12,PINK,600)
        card(268,750,1128,236)
        for i,row in enumerate([('Weekly groceries','Alex · Today','$86.40','Food'),('Books for the weekend','Alex · Yesterday','$30.00','Personal'),('Fuel for the week','Jamie · Nov 4','$42.00','Gas')]):
            purchase_row(292,773+i*69,1074,*row)
            if i<2: line(292,826+i*69,1372,826+i*69)
    finish('Dashboard',m)

def purchases(m):
    shell('Purchases',m); title('Purchases','The everyday things, all in one place.',m,'+  Add purchase')
    if m:
        button(20,194,'+  Add purchase',350)
        card(20,252,350,45); icon(33,263,'search',MUTED,19); text(62,280,'Search purchases',12,MUTED)
        pill(20,312,'November 2026',fill='white',color=INK); pill(161,312,'All categories  ⌄',fill='white',color=INK)
        text(20,381,'$2,360 recorded this month',14,INK,600)
        text(20,421,'TODAY · NOV 6',10,MUTED,600)
        card(20,439,350,84); purchase_row(36,461,317,'Weekly groceries','Alex · Food','$86.40','Food',True)
        text(20,561,'YESTERDAY · NOV 5',10,MUTED,600)
        card(20,579,350,152)
        purchase_row(36,599,317,'Books for the weekend','Alex · Personal / Books','$30.00','Personal',True)
        line(36,650,354,650); purchase_row(36,671,317,'Dinner together','Jamie · Dates','$60.00','Dates',True)
        card(20,752,350,149,CLAY)
        pill(36,768,'Pending sync',CLAY,'#855a37')
        text(36,824,'Coffee beans',15,INK,600); text(285,824,'$18.00',14,INK,600)
        text(36,852,'Alex · Food · Saved on this device',11,MUTED)
        text(36,878,'Not yet included in shared totals.',11,MUTED)
    else:
        card(268,198,1128,80)
        icon(290,226,'search',MUTED,20); text(322,243,'Search purchases',13,MUTED)
        pill(695,223,'November 2026  ⌄','white',INK); pill(867,223,'All categories  ⌄','white',INK); pill(1041,223,'All people  ⌄','white',INK)
        text(268,325,'November purchases',25,INK,500,True); text(1151,323,'$2,360 recorded',15,INK,600)
        card(268,349,1128,476)
        for x,label in [(292,'PURCHASE'),(752,'CATEGORY'),(971,'ADDED BY'),(1138,'DATE'),(1284,'AMOUNT')]: text(x,381,label,10,MUTED,600)
        line(292,399,1372,399)
        rows=[('Weekly groceries','Receipt attached','Food','Alex','Nov 6','$86.40'),('Books for the weekend','Personal / Books','Personal · Alex','Alex','Nov 5','$30.00'),('Dinner together','A Friday favorite','Dates','Jamie','Nov 5','$60.00'),('Fuel for the week','—','Gas','Jamie','Nov 4','$42.00'),('Monthly rent','Linked recurring bill','Housing','Alex','Nov 1','$1,500.00')]
        for i,(name,detail,cat,person,date,amt) in enumerate(rows):
            y=430+i*79
            text(292,y,name,14,INK,600); text(292,y+22,detail,11,MUTED)
            text(752,y+9,cat,12,MUTED); text(971,y+9,person,12,MUTED); text(1138,y+9,date,12,MUTED); text(1270,y+9,amt,13,INK,600)
            if i<4: line(292,y+43,1372,y+43)
        card(268,847,1128,101,CLAY); pill(290,862,'1 pending sync',CLAY,'#855a37')
        text(290,918,'Coffee beans · $18.00 · Alex',13,INK,600); text(692,918,'Saved on this device. Not yet included in shared totals.',12,MUTED)
    finish('Purchases',m)

def budget(m):
    shell('Budget',m); title('Budget','A simple plan for the month ahead.',m,'Edit allocations')
    categories=[('Housing',1500,1500),('Food',600,287),('Gas',200,142),('Dates',200,60),('Phone',100,100),('Car insurance',180,180),('Personal · Alex',200,50),('Personal · Jamie',200,41)]
    if m:
        pill(20,192,'November 2026  ⌄','white',INK)
        card(20,237,350,143,BLUSH); text(38,268,'MONTHLY ALLOCATIONS',10,PINK,600); text(38,311,'$3,180',36,INK,500,True)
        text(38,343,'Spent $2,360  ·  Remaining $820',11,MUTED)
        button(20,397,'Edit allocations',350,False)
        text(20,481,'Spending categories',23,INK,500,True)
        card(20,501,350,356)
        for i,(name,a,s) in enumerate(categories[:4]+[categories[6]]):
            y=526+i*65
            text(36,y,name,13,INK,600); text(256,y,f'${a-s:,} left',12,INK,600)
            progress(36,y+13,185,min(s/a,1),'#9aa98b'); text(234,y+22,f'${s:,} / ${a:,}',10,MUTED)
        text(20,890,'View all categories  →',12,PINK,600)
        text(20,926,'Income, bills & savings  →',12,PINK,600)
    else:
        pill(268,195,'‹   November 2026   ›','white',INK)
        for x,label,val,sub,fill in [(268,'Allocated','$3,180','Across household categories','white'),(650,'Spent','$2,360','Recorded spending','white'),(1032,'Remaining','$820','Within this month’s plan',BLUSH)]:
            card(x,244,364,135,fill); text(x+22,274,label,12,MUTED,600); text(x+22,320,val,34,INK,500,True); text(x+22,351,sub,11,MUTED)
        card(268,405,744,582)
        text(290,445,'Spending categories',23,INK,500,True)
        text(290,481,'CATEGORY',10,MUTED,600); text(658,481,'ALLOCATED',10,MUTED,600); text(798,481,'SPENT',10,MUTED,600); text(904,481,'LEFT',10,MUTED,600)
        for i,(name,a,s) in enumerate(categories):
            y=521+i*56
            text(290,y,name,13,INK,600); text(658,y,f'${a:,}',13); text(798,y,f'${s:,}',13,MUTED); text(904,y,f'${a-s:,}',13,INK,600)
            progress(290,y+12,292,s/a,'#9aa98b')
        card(1032,405,364,220,SAGE)
        text(1054,441,'Personal, still part of the plan',17,INK,500,True)
        text(1054,477,'Alex’s allowance',13,INK,600); text(1054,513,'$150 remaining',26,INK,500,True)
        text(1054,550,'Books $30 · Hobbies $20',11,MUTED)
        text(1054,585,'Included once in household spending.',11,MUTED)
        card(1032,645,364,216)
        text(1054,683,'The rest of your plan',22,INK,500,True)
        for i,label in enumerate(['Income','Recurring bills','Savings']):
            text(1054,726+i*45,label,14,INK,600); icon(1349,710+i*45,'arrow',PINK,18)
        text(1032,900,'Savings allocation · $0 this month',11,MUTED); text(1032,919,'Contributions are tracked separately.',11,MUTED)
    finish('Budget',m)

def wishlist(m):
    shell('Wish lists',m); title('Wish lists','A little room for what’s next.',m,'+  Add item')
    if m:
        button(20,192,'+  Add item',350)
        pill(20,253,'Everyone',BLUSH,PINK); pill(113,253,'Alex','white',INK); pill(180,253,'Jamie','white',INK)
        text(20,318,'Household wish list',22,INK,500,True)
        for i,(name,price,owner,desc,fill) in enumerate([('A quieter morning','$120','Alex','A burr grinder for better coffee.',SAGE),('Living room lamp','$85','Jamie','A warm glow for the reading corner.',CLAY),('Weekend in the woods','$240','Alex','A cabin, a book, and nowhere to be.',BUTTER)]):
            y=339+i*195
            card(20,y,350,176)
            rect(36,y+17,42,42,fill,13); text(49,y+45,['☕','✧','⌂'][i],22,GREEN)
            text(92,y+35,name,14,INK,600); text(92,y+55,owner,11,MUTED)
            text(36,y+91,desc,11,MUTED); text(36,y+131,price,25,INK,500,True)
            text(219,y+132,'View item  →',12,PINK,600)
    else:
        pill(268,201,'Everyone',BLUSH,PINK); pill(366,201,'Alex','white',INK); pill(440,201,'Jamie','white',INK)
        pill(1247,201,'Active  ⌄','white',INK)
        text(268,281,'Household wish list',25,INK,500,True); text(268,310,'Little ideas. Shared possibilities.',13,MUTED)
        for i,(name,price,owner,desc,fill,symbol) in enumerate([('A quieter morning','$120','Alex','A burr grinder for better coffee.',SAGE,'☕'),('Living room lamp','$85','Jamie','A warm glow for the reading corner.',CLAY,'✧'),('Weekend in the woods','$240','Alex','A cabin, a book, and nowhere to be.',BUTTER,'⌂')]):
            x=268+i*382
            card(x,339,364,420)
            rect(x+16,355,332,130,fill,12)
            text(x+150,442,symbol,64,GREEN if i==0 else '#906b52',400,True)
            text(x+22,523,name,25,INK,500,True); text(x+22,553,desc,11,MUTED)
            pig(x+22,574,30); text(x+62,594,owner,12,MUTED)
            text(x+22,650,price,32,INK,500,True)
            button(x+22,683,'View item',320,False)
        card(268,793,1128,126,BLUSH)
        text(292,831,'From “someday” to a shared plan.',25,INK,500,True)
        text(292,864,'Open an item to request approval or record a purchase when you’re ready.',13,MUTED)
        text(292,890,'A wish-list item does not reserve money or record spending.',11,MUTED)
    finish('Wish lists',m)

def approvals(m):
    shell('Approvals',m); title('Approvals','Make room for a shared yes.',m,'+  New request')
    if m:
        button(20,192,'+  New request',350)
        pill(20,252,'Needs you · 1',BLUSH,PINK); pill(148,252,'All requests','white',INK)
        card(20,300,350,421)
        pill(38,318,'Awaiting your approval',BUTTER,'#786439')
        text(38,380,'Living room lamp',28,INK,500,True); text(38,411,'Requested by Jamie · Nov 5',11,MUTED)
        text(38,463,'$85.00',38,INK,500,True); text(38,490,'Proposed category · Housing',11,MUTED)
        text(38,532,'A warm glow for the reading corner.',11,MUTED)
        line(38,556,352,556)
        text(38,587,'Your approval',14,INK,600)
        rect(294,566,54,30,'#ded4d0',15); rect(298,570,22,22,'white',11)
        text(38,616,'Not approved',11,MUTED)
        text(38,654,'0 of 1 required approvals',12,INK,600)
        text(38,681,'All other household members must approve.',10,MUTED)
        card(20,741,350,147,SAGE)
        pill(38,759,'Approved',SAGE,GREEN)
        text(38,816,'Picnic basket',22,INK,500,True)
        text(38,845,'Alex · $60.00 · Jamie approved',11,MUTED)
        text(20,926,'Approval doesn’t record a purchase.',11,MUTED)
    else:
        pill(268,201,'Needs you · 1',BLUSH,PINK); pill(398,201,'All requests','white',INK); pill(521,201,'My requests','white',INK)
        card(268,258,722,583)
        pill(292,281,'Awaiting your approval',BUTTER,'#786439')
        text(292,351,'Living room lamp',35,INK,500,True)
        pig(292,374,34); text(338,396,'Jamie requested · November 5',12,MUTED)
        text(292,468,'$85.00',43,INK,500,True); text(292,505,'Proposed category · Housing',12,MUTED)
        text(292,555,'A warm glow for the reading corner.',15,INK)
        text(292,590,'View item link ↗',12,PINK,600)
        line(292,620,966,620)
        text(292,659,'Your approval',16,INK,600); text(292,687,'Not approved',12,MUTED)
        rect(900,640,60,34,'#ded4d0',17); rect(904,644,26,26,'white',13)
        text(292,740,'0 of 1 required approvals',14,INK,600)
        text(292,770,'All active household members other than Jamie must approve.',12,MUTED)
        text(292,805,'Comments · 0',12,PINK,600)
        card(1010,258,386,259,SAGE)
        pill(1034,279,'Approved',SAGE,GREEN)
        text(1034,344,'Picnic basket',27,INK,500,True)
        text(1034,379,'Alex requested · $60.00',12,MUTED)
        text(1034,414,'Jamie approved · 1 of 1',12,GREEN,600)
        button(1034,449,'Record purchase',338,False)
        card(1010,539,386,194)
        text(1034,577,'An agreement, together.',24,INK,500,True)
        text(1034,617,'Approval does not reserve money',12,MUTED)
        text(1034,643,'or record spending. Add the actual',12,MUTED)
        text(1034,669,'purchase when it happens.',12,MUTED)
        text(268,890,'Showing the selected profile’s approval. The requester cannot approve their own request.',12,MUTED)
    finish('Approvals',m)

for screen in [dashboard,purchases,budget,wishlist,approvals]:
    for mobile in [False,True]: screen(mobile)

# Separate corner notification list, shown over the dashboard.
shell('Dashboard',False)
title('Good morning, Alex','Here’s what’s happening with your household.')
card(268,232,1128,195,BLUSH); text(295,278,'Your November plan',25,INK,500,True); text(295,335,'$820 remaining',42,INK,500,True)
rect(950,91,454,525,'#f1e6e3',20)
card(940,84,454,525)
text(966,125,'Notifications',25,INK,500,True); text(1265,124,'Mark all read',11,PINK,600)
line(964,147,1370,147)
for i,(heading,l1,l2,time) in enumerate([
    ('A shared yes?','Jamie requested approval for a lamp.','Open request →','12 min ago'),
    ('Something for someday','Jamie added an item to the wish list.','Open wish list →','1 hour ago'),
    ('You’re on the same page','Jamie approved Picnic basket.','Open request →','Yesterday')]):
    y=177+i*132
    rect(963,y-10,7,7,PINK,4); text(984,y,heading,14,INK,600); text(984,y+27,l1,11,MUTED); text(984,y+54,l2,11,PINK,600); text(984,y+77,time,10,MUTED)
    if i<2: line(964,y+98,1370,y+98)
parts.append('</svg>')
(OUT/'notifications-desktop.svg').write_text(''.join(parts))
subprocess.run(['rsvg-convert',str(OUT/'notifications-desktop.svg'),'-o',str(OUT/'notifications-desktop.png')],check=True)

# Mobile corner notifications, separate from the five navigation destinations.
shell('Dashboard',True)
title('Good morning, Alex','Here’s your household at a glance.',True)
card(20,194,350,154,BLUSH)
text(38,231,'LEFT IN THIS MONTH’S PLAN',10,PINK,600)
text(38,286,'$820',43,INK,500,True)
rect(12,100,370,598,'#f1e6e3',18)
card(8,96,370,598)
text(28,137,'Notifications',25,INK,500,True)
text(28,170,'Mark all read',12,PINK,600)
line(28,191,358,191)
for i,(heading,l1,l2,time) in enumerate([
    ('A shared yes?','Jamie requested approval for a lamp.','Open request →','12 min ago'),
    ('Something for someday','Jamie added an item to the wish list.','Open wish list →','1 hour ago'),
    ('You’re on the same page','Jamie approved Picnic basket.','Open request →','Yesterday')]):
    y=228+i*148
    rect(28,y-9,7,7,PINK,4)
    text(46,y,heading,14,INK,600)
    text(46,y+29,l1,11,MUTED)
    text(46,y+59,l2,12,PINK,600)
    text(46,y+87,time,10,MUTED)
    if i<2: line(28,y+113,358,y+113)
finish('Notifications',True)

# A small review sheet, kept legible by linking each full-resolution screen.
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1700" height="1270" viewBox="0 0 1700 1270">',f'<rect width="1700" height="1270" fill="{BG}"/>',f'<text x="40" y="58" font-family="Liberation Serif" font-size="36" fill="{INK}">PigPen / a softer space for shared plans</text>',f'<text x="40" y="90" font-family="DejaVu Sans" font-size="15" fill="{MUTED}">Direction 01 · Blush, warm paper &amp; earthy pastels · Desktop + mobile studies</text>']
for i,name in enumerate(['dashboard','purchases','budget','wish-lists','approvals']):
    x=40+i*330
    svg.append(f'<text x="{x}" y="140" font-family="DejaVu Sans" font-size="16" fill="{INK}">{["Dashboard","Purchases","Budget","Wish lists","Approvals"][i]}</text>')
    for form,y,w,h in [('desktop',160,310,224),('mobile',412,250,667)]:
        data=base64.b64encode((OUT/f'{name}-{form}.svg').read_bytes()).decode()
        svg.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/svg+xml;base64,{data}"/>')
for i,(label,color) in enumerate([('Warm blush',BG),('Soft pink',BLUSH),('Rose',PINK),('Sage',SAGE),('Clay',CLAY),('Butter',BUTTER)]):
    x=40+i*264
    svg.append(f'<rect x="{x}" y="1135" width="236" height="45" rx="12" fill="{color}" stroke="{LINE}"/><text x="{x}" y="1208" font-family="DejaVu Sans" font-size="13" fill="{MUTED}">{label} / {color}</text>')
svg.append('</svg>'); (OUT/'overview.svg').write_text(''.join(svg))
subprocess.run(['rsvg-convert',str(OUT/'overview.svg'),'-o',str(OUT/'overview.png')],check=True)

names=['dashboard','purchases','budget','wish-lists','approvals']
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PigPen · Design direction 01</title><style>body{margin:0;background:#fff8f7;color:#382e2d;font:16px system-ui}header,main{max-width:1440px;margin:auto;padding:32px}h1,h2{font-family:Georgia,serif;font-weight:400}h1{font-size:42px}a{color:#a94665}nav{display:flex;gap:24px;flex-wrap:wrap}section{margin-top:60px}img{max-width:100%;border:1px solid #eadedb;border-radius:12px}.views{display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:28px;align-items:start}.mobile{width:290px}small{color:#827572} @media(max-width:800px){.views{grid-template-columns:1fr}.mobile{width:390px;max-width:100%}header,main{padding:20px}} </style><header><small>PIGPEN · STATIC MOCKUPS · DIRECTION 01</small><h1>A softer space for shared plans.</h1><p>Gusto-inspired space and typography, warm blush backgrounds, rose accents, and earthy pastels.</p><p>Illustrative data · Controls are part of the artwork · No app features or backend connections</p><nav>'''
page+=''.join(f'<a href="#{n}">{n.replace("-"," ").title()}</a>' for n in names)
page+='</nav></header><main>'
for n in names:
    page+=f'<section id="{n}"><h2>{n.replace("-"," ").title()}</h2><div class="views"><a href="{n}-desktop.png"><img alt="Desktop {n} mockup" src="{n}-desktop.svg"></a><a href="{n}-mobile.png"><img class="mobile" alt="Mobile {n} mockup" src="{n}-mobile.svg"></a></div></section>'
page+='<section><h2>Corner notification list</h2><div class="views"><img alt="Desktop notification list open from the header" src="notifications-desktop.svg"><img class="mobile" alt="Mobile notification list open from the header" src="notifications-mobile.svg"></div></section><p>Full-resolution PNG and editable SVG copies accompany every view. See README.md for decisions and remaining assumptions.</p></main></html>'
(OUT/'index.html').write_text(page)
print('Built 10 screen mockups, notification example, overview, and static review page.')
