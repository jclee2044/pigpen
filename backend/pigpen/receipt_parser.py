"""Conservative receipt suggestions; no HTTP, database or OCR dependencies."""
import calendar
import re
from datetime import datetime, date
from decimal import Decimal

PARSER_VERSION = '10'
PRICE = re.compile(r'(?<![\d.,])\$?(-?(?:\d{1,6}(?:,\d{3})*)?\.\d{2})(?!\d)')
SUMMARY = re.compile(r'\b(sub[ -]*total|subtctal|supbttal|sub/tt[1l]|original\s+ttl|sub\s*w|total|tota|tctal|totl|jotal|tax\w*|txtl|tip|gratuity|discount|coupon|savings|change|chng|cash|tend\w*|balance|visa|mastercard|debit|credit|payment|paid|amt\s+due|amount\s+due|ser[vu]ice(?:\s*\d|\s+charge|\s+fee)|serv\.|processing\s+fee|atm\s+charge|counter[- ](?:eat|take)|carry\s*out|delivery\s+charge)\b', re.I)
HEADER = re.compile(r'\b(for a chance|survey|discover|store|served|place your|waiter|duplicate|demo\s+system|acct|auth|trans(?:action)?|card|seat|amount|guest\w*|server|date|table|cashier|check|order|receipt|invoice|thank\w*|welcome|tel|te1|phone|fax|terminal|register|station|qty|dine|dessert|beverage)\b|https?://|www\.|\b\d{5}(?:-\d{4})?\b|\d.*\b(st|street|ave|avenue|road|rd|blvd|drive|dr|hwy|turnpike)\b', re.I)
TOTAL = re.compile(r'(take[- ]out\s+total|receipt\s+total|grand\s+total|total(?:\s+(?:sale|due|amount|paid))?|totl|tota|tctal|jotal|(?:amount|a[mn]t|balance)\s+due)', re.I)


def expiry(stored_at):
    stamp = datetime.fromisoformat(stored_at.replace('Z', '+00:00'))
    year, month = divmod(stamp.year * 12 + stamp.month - 1 + 3, 12)
    return stamp.replace(year=year, month=month+1, day=min(stamp.day, calendar.monthrange(year, month+1)[1])).isoformat()


def money(text):
    # OCR sometimes reads a decimal point as a comma after an explicit dollar
    # sign. Keep thousands separators and unmarked comma amounts untouched.
    text=re.sub(r'(\$\s*\d{1,6}),(\d{2})(?![\d.,])',r'\1.\2',text)
    return [(m, int(Decimal(m.group(1).replace(',', '')) * 100)) for m in PRICE.finditer(text)]


def receipt_dates(text):
    values=[]
    # This USD parser uses US month/day ordering and 2000–2099 for two-digit years.
    patterns=[(r'\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b',(1,2,3)),
              (r'\b(\d{1,2})[-/](\d{1,2})[-/]((?:20)?\d{2})\b',(3,1,2))]
    for pattern,order in patterns:
        for m in re.finditer(pattern,text):
            y,mo,d=(int(m.group(i)) for i in order)
            try: values.append(date(y+2000 if y<100 else y,mo,d).isoformat())
            except ValueError: pass
    for pattern,formats in [(r'\b\d{1,2}-[A-Za-z]{3}-20\d{2}\b',['%d-%b-%Y']),
                            (r'\b[A-Za-z]{3}\.\d{1,2}\s+\d{2}\b',['%b.%d %y'])]:
        for m in re.finditer(pattern,text):
            for fmt in formats:
                try: values.append(datetime.strptime(m.group(),fmt).date().isoformat())
                except ValueError: pass
    return values


def parse_receipt(lines):
    lines = [x for x in lines if x.get('text', '').strip()]
    # Pair a wrapped label with an immediately following price only when the
    # adapter retained spatial evidence. Never join arbitrary plain text rows.
    joined=[]
    for line in lines:
        text=line['text'].strip()
        if joined and re.fullmatch(r'\$?\s*\d+\.\d{2}',text) and not money(joined[-1]['text']):
            previous=joined[-1]
            if 'y' in line and 'y' in previous and 0 < line['y']-previous['y'] <= max(line['height'],previous['height'])*1.2:
                joined[-1]={**previous,'text':previous['text']+' '+text,'score':min(previous['score'],line['score']),
                            'tokens':previous.get('tokens',[])+line.get('tokens',[])}
                continue
        joined.append(line)
    lines=joined
    texts = [x['text'].strip() for x in lines]
    warnings = ['Review the receipt, including handwritten changes, and every suggested field before saving. Amounts are in USD; verify the receipt currency.']
    totals, items, dates, subtotals, taxes, payments, service_totals = [], [], [], [], [], [], []
    adjustments=[]
    trailing_amounts=[]
    last_total_index=-1
    tip_guide=False
    cash=[]
    changes=[]
    paid_totals=[]
    merchant = None
    unsupported = any(re.search(r'€|£|\b(EUR|GBP|CAD|AUD|JPY|MYR|SGD|INR|NZD|CHF|RM|Rs|RS|RUPEES|EURO|SDN BHD)\b', t) for t in texts)
    unsupported = unsupported or any(re.search(r'\b[A-Z]\d[A-Z]\s+\d[A-Z]\d\b',t) for t in texts[:12])
    payments=[v for t in texts if re.search(r'\b(?:cash|visa|vssa|mastercard|debit|credit|paid|payments?|atm)\b',t,re.I) and (p:=money(t)) for _,v in p[-1:]]
    item_region_ended=False
    blank_tip=False
    for index, (line, text) in enumerate(zip(lines, texts)):
        confidence = line.get('score', 0)
        prices = money(text)
        merchant_text=re.sub(r'\s+check\s+[#\d].*$', '', text, flags=re.I)
        if index < 8 and merchant is None and confidence >= .85 and not prices and '$' not in text and not re.match(r'\d{3}',text) and not HEADER.search(merchant_text) and not SUMMARY.search(text) and re.search(r'[a-zA-Z]{3}',merchant_text) and merchant_text.strip(' -*').lower() not in ('the','place','restaurant','restaurants','grille','bar','indian cuisine','family restaurant','restaurants, inc.','city, state zip') and not re.search(r'\d{2}:\d{2}|\d[-/]\d',text):
            merchant = re.sub(r'\s+\d{1,2}:\d{2}\s*(?:AM|PM).*$', '', merchant_text, flags=re.I).strip(' #*')[:200]
        dates.extend(receipt_dates(text))
        if re.search(r'suggested|recommended|tip guide|tip helper',text,re.I):tip_guide=True
        if re.fullmatch(r'(?:tip|gratuity|total)[\s:$_.-]*',text,re.I):
            blank_tip=True
        if not prices:
            continue
        last,value=prices[-1]
        label=text[:last.start()].strip(' .$:*:')
        label=re.sub(r'^(?:\d{1,2}/\d{1,2}\s+)?\d{1,2}:\d{2}\s*(?:[ap](?:m)?)?\s*','',label,flags=re.I)
        # A misread currency glyph can sit between a total label and its price.
        if re.fullmatch(r'total\s+[0-9]',label,re.I) and value in payments:label='TOTAL'
        if prices and re.search(r'\b(?:tip|gratuity|service charge|processing fee|surcharge)\b',label,re.I) and not re.search(r'suggest|guide|not included',label,re.I):adjustments.append(value)
        if re.fullmatch(r'cash',label,re.I):cash.append(value)
        if re.fullmatch(r'change(?:\s+due)?',label,re.I):changes.append(value)
        if re.fullmatch(r'payment',label,re.I):paid_totals.append((value,confidence,confidence,text))
        suffix=re.search(r'\btotal\s+paid$',label,re.I)
        if suffix and value in payments and item_region_ended:label='total paid'
        if label.endswith('S') and TOTAL.fullmatch(label[:-1].strip(' :')):label=label[:-1].strip(' :')
        if TOTAL.fullmatch(label):
            last_total_index=index
            tip_guide=False
            # A low-confidence label is usable only if independently corroborated.
            tokens=line.get('tokens',[])
            price_score=next((t['score'] for t in reversed(tokens) if money(t['text'])),confidence)
            totals.append((value,confidence,price_score,text))
            item_region_ended=True
        elif re.search(r'\b(?:sub[ -]*total|subtctal|supbttal|sub/tt[1l]|original\s+ttl)\b',label,re.I):
            subtotals.append(value);item_region_ended=True
        elif re.fullmatch(r'(?:to[- ]go|drive\s+thru)',label,re.I):
            service_totals.append((value,confidence,confidence,text));item_region_ended=True
        elif SUMMARY.search(label):
            if re.fullmatch(r'(?:sales\s+)?tax(?:\s*\d+)?(?:\s*\(?[\d.]+%\)?)?',label,re.I):taxes.append(value)
            if re.search(r'\b(cash|visa|mastercard|debit|credit|paid)\b',label,re.I):payments.append(value)
            if not re.search(r'\b(coupon|discount|savings)\b',label,re.I):item_region_ended=True
        elif not tip_guide and last_total_index>=0:
            trailing_amounts.append((index,value))
        elif not item_region_ended and label and re.search('[a-zA-Z]',label) and confidence >= .85 and value > 0 and not HEADER.search(label) and not text[last.end():].lstrip().startswith(('-',')')) and '(' not in text[max(0,last.start()-2):last.start()]:
            # In a unit/extended-price row, retain the rightmost printed price.
            label=text[:prices[0][0].start()].strip(' .$:*:')
            label=re.sub(r'\s+\d{8,}[A-Z]*\b.*$','',label).strip()
            if re.fullmatch(r'(?:food|items|bar)',label,re.I):continue
            if label:items.append({'description': label, 'line_total_minor': value})
    corroborated=set(payments)
    arithmetic_total=subtotals[0]+sum(taxes) if len(set(subtotals))==1 and taxes else None
    if arithmetic_total is not None:corroborated.add(arithmetic_total)
    if len(cash)==1 and len(changes)==1:
        corroborated.add(cash[0]-changes[0])
    totals.extend(t for t in paid_totals if len(cash)==1 and len(changes)==1 and t[0]==cash[0]-changes[0])
    # A settled zero balance does not negate a corroborated printed paid total.
    if any(v>0 and v in payments for v,_,_,_ in totals):
        totals=[t for t in totals if t[0]!=0 or not re.match(r'(?:amount|amt|balance)\s+due',t[3],re.I)]
    totals.extend(t for t in service_totals if t[0] in corroborated)
    values={v for v,score,price_score,_ in totals if v>0 and (score>=.9 or (price_score>=.9 and v in corroborated) or (score>=.85 and v in payments and v==arithmetic_total))}
    amount=next(iter(values)) if len(values)==1 and all(v in values for v,_,_,_ in totals) else None
    # A separately printed balance may corroborate the aggregate of seat totals.
    if amount is None and totals and re.match(r'balance\s+due',totals[-1][3],re.I):
        final=totals[-1][0]
        preceding=[]
        for value,score,_,_ in totals[:-1]:
            if score>=.9 and value!=final:preceding.append(value)
        if preceding and sum(preceding)==final and totals[-1][1]>=.9:amount=final
    receipt_totals=[v for v,score,_,t in totals if re.match(r'receipt\s+total',t,re.I) and score>=.9]
    if len(set(receipt_totals))==1:
        amount=receipt_totals[0]
    # Distinct before/after-tip totals need exact printed arithmetic evidence.
    distinct_totals=[]
    for total in totals:
        if not distinct_totals or total[0]!=distinct_totals[-1][0]:distinct_totals.append(total)
    if amount is None and len(distinct_totals)==2 and len(adjustments)==1:
        first,last=distinct_totals
        if first[0]+adjustments[0]==last[0] and first[1]>=.9 and last[1]>=.9:amount=last[0]
    discounts=any(re.search(r'\b(discount|coupon|savings|complimentary|comps?|offer)\b|\d\.\d{2}\s*-|\(\$?\d+\.\d{2}\)',t,re.I) for t in texts)
    if amount is not None and items and sum(x['line_total_minor'] for x in items)>amount and not discounts and not receipt_totals and amount not in corroborated:
        amount=None
        warnings.append('Item amounts conflict with the printed total. Enter the verified charged amount.')
    if amount is not None and any(i>last_total_index and value>amount for i,value in trailing_amounts):
        amount=None
        warnings.append('Another amount appears after the printed total. Check handwritten changes and enter the final charged amount.')
    if unsupported:
        amount = None
        warnings.append('Unsupported or ambiguous currency. Enter the USD amount manually.')
    if blank_tip:
        amount = None
        warnings.append('Receipt has an unfilled tip or total line. Enter the final paid total.')
    elif any(re.search(r'\b(tip|gratuity)\b',t,re.I) for t in texts):
        warnings.append('Check that the printed total includes the final tip, including any handwritten changes.')
    if amount is None:
        warnings.append('No unambiguous final total found. Enter the total from the receipt.')
    if items and subtotals and sum(x['line_total_minor'] for x in items)>2*max(subtotals):
        items=[]
        warnings.append('Item prices could not be matched reliably. Add line items manually if needed.')
    if items:
        warnings.append('Line items may be incomplete or misread. Check descriptions and prices; taxes, fees and discounts are not itemized here.')
    if items and amount and sum(x['line_total_minor'] for x in items) > amount:
        warnings.append('Recognized items exceed the total; check discounts and item prices.')
    description = '\n'.join(f"{x['description']} — ${x['line_total_minor']/100:.2f}" for x in items)
    if len(description)>4000:
        warnings.append('Line items exceed the description limit. Shorten the description before saving.')
    return {'item': items[0]['description'][:200] if len(items)==1 else f'Purchase at {merchant}'[:200] if merchant else 'Receipt purchase',
            'merchant':merchant,'amount_minor':amount,'transaction_date':dates[0] if len(set(dates))==1 else None,
            'description':description,'line_items':items,'warnings':warnings,
            'evidence':{'total_lines':[t for _,_,_,t in totals]},'parser_version':PARSER_VERSION}
