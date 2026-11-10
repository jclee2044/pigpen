"""Synthetic regressions for real-world layouts, without storing receipt text."""
from pigpen.receipt_parser import parse_receipt


def rows(*texts):
    return [{'text':text,'score':.99} for text in texts]


def test_total_variants_and_paid_gratuity():
    for label in ['TOTL','Amt Due','TOTAL DUE','Balance Due']:
        result=parse_receipt(rows('LOCAL CAFE','Tea .75','Subtotal .75','Gratuity .15',f'{label} .90','Visa .90'))
        assert result['amount_minor']==90
        assert result['line_items']==[{'description':'Tea','line_total_minor':75}]
    assert parse_receipt(rows('Total 10.00','Tip ____'))['amount_minor'] is None


def test_low_confidence_total_needs_independent_evidence():
    total={'text':'Jotal 10.80','score':.6,'tokens':[{'text':'Jotal','score':.6},{'text':'10.80','score':.99}]}
    assert parse_receipt([total])['amount_minor'] is None
    assert parse_receipt([*rows('Subtotal 10.00','Tax .80'),total])['amount_minor']==1080
    assert parse_receipt([*rows('Subtotal 11.00','Tax .80'),total])['amount_minor'] is None


def test_headers_unit_prices_discounts_and_fees():
    result=parse_receipt(rows('YOUR GUEST NUMBER IS','24','Guests Server','CAFE42','2 Tea 2.00 4.00','COUPON 1.00-0','Cake 3.00','Subtotal 6.00','RESORT TAX2% .12','SERUICE20% 1.20','TOTAL 7.32'))
    assert result['merchant']=='CAFE42'
    assert result['line_items']==[{'description':'2 Tea','line_total_minor':400},{'description':'Cake','line_total_minor':300}]
    assert result['amount_minor']==732


def test_dates_and_absent_business_name():
    assert parse_receipt(rows('123 Main Street','Somewhere, CA 90000','[Seat 1]','TOTAL 1.00'))['merchant'] is None
    for text,expected in [('02/03/19','2019-02-03'),('01-27-2018','2018-01-27'),('30-Aug-2019','2019-08-30')]:
        assert parse_receipt(rows(text))['transaction_date']==expected
    assert parse_receipt(rows('02/03/19','02/04/19'))['transaction_date'] is None
    assert parse_receipt(rows('02/30/19'))['transaction_date'] is None


def test_ambiguous_money_and_final_totals_stay_blank():
    assert parse_receipt(rows('TOTAL 1.000'))['amount_minor'] is None
    assert parse_receipt(rows('TOTAL 1.00','TOTAL 2.00'))['amount_minor'] is None
    assert parse_receipt(rows('TOTAL €1.00'))['amount_minor'] is None


def test_time_prefix_aggregate_seats_and_service_total():
    assert parse_receipt(rows('09:38PM TOTAL 11.91'))['amount_minor']==1191
    assert parse_receipt(rows('Total 20.62','Total 13.13','Total 33.75','Balance Due 33.75'))['amount_minor']==3375
    assert parse_receipt(rows('Total 20.62','Total 12.13','Balance Due 33.75'))['amount_minor'] is None
    assert parse_receipt(rows('TO-GO 13.78','Visa 13.78'))['amount_minor']==1378
    assert parse_receipt(rows('TO-GO 13.78'))['amount_minor'] is None


def test_trailing_discount_is_not_positive_merchandise():
    result=parse_receipt(rows('Pie 19.98','Birthday offer 5.00-','Subtotal 14.98','TOTAL 14.98'))
    assert result['line_items']==[{'description':'Pie','line_total_minor':1998}]


def test_receipt_share_and_printed_tip_are_distinguished():
    assert parse_receipt(rows('Total 77.49','Receipt Total 38.75'))['amount_minor']==3875
    assert parse_receipt(rows('Total 43.60','Voluntary 18% Tip 7.20','Total 50.80'))['amount_minor']==5080
    assert parse_receipt(rows('Total 43.60','Suggested Tip 7.20','Total 50.80'))['amount_minor'] is None
    assert parse_receipt(rows('Total 43.60','Tip 7.20','Total 60.80'))['amount_minor'] is None
    assert parse_receipt(rows('Offer (8.99)','Combo, Onion (0.75)','TOTAL 10.00'))['line_items']==[]


def test_wrapped_total_needs_layout_evidence():
    assert parse_receipt(rows('TOTAL','10.00'))['amount_minor'] is None
    wrapped=[{'text':'TOTAL','score':.99,'y':100,'height':20}, {'text':'10.00','score':.99,'y':120,'height':25}]
    assert parse_receipt(wrapped)['amount_minor']==1000
    wrapped[1]['y']=150
    assert parse_receipt(wrapped)['amount_minor'] is None


def test_settled_balance_and_additional_service_charge():
    assert parse_receipt(rows('Total 52.47','Payments 52.47','Amount Due 0.00'))['amount_minor']==5247
    assert parse_receipt(rows('Total 52.47','Amount Due 0.00'))['amount_minor'] is None
    assert parse_receipt(rows('Total 24.36','Service Charge 8.90','Total 33.26'))['amount_minor']==3326
    assert parse_receipt(rows('Total 55.51','Gratuity 9.01','Total 64.52','Balance Due 64.52'))['amount_minor']==6452
    assert parse_receipt(rows('12/20 14:29 TOTAL 47.09'))['amount_minor']==4709
    assert parse_receipt(rows('Cash 13.25','Payment 13.12','Change Due .13'))['amount_minor']==1312
    assert parse_receipt(rows('Payment 13.12'))['amount_minor'] is None
    assert parse_receipt(rows('Take-Out Total 7.27'))['amount_minor']==727


def test_currency_hints_and_unreliable_item_prices():
    assert parse_receipt(rows('Grand Total Rs. 617.00','TOTAL 617.00'))['amount_minor'] is None
    assert parse_receipt(rows('Edmonton AB T5P 4A9','TOTAL 26.15'))['amount_minor'] is None
    assert parse_receipt(rows('AM Dining Rm','TOTAL 26.96'))['amount_minor']==2696
    result=parse_receipt(rows('Wine 822.50','Pizza 827.00','Subtotal 49.50','Tax 2.97','Total 52.47'))
    assert result['line_items']==[] and result['amount_minor']==5247


def test_currency_glyph_in_explicit_total_label():
    assert parse_receipt(rows('Total: S93.58'))['amount_minor']==9358
    assert parse_receipt(rows('Soda S2.00'))['amount_minor'] is None


def test_unlabeled_later_amount_may_be_handwritten_final_total():
    result=parse_receipt(rows('Subtotal 131.00','Tax 12.71','Total 143.71','Thank you 153.71'))
    assert result['amount_minor'] is None
    assert parse_receipt(rows('Total 10.00','Cash 20.00','Change 10.00'))['amount_minor']==1000
    assert parse_receipt(rows('Total 10.00','Suggested tips','20% 2.00 12.00'))['amount_minor']==1000


def test_conflicting_item_amounts_do_not_become_a_small_tax_total():
    assert parse_receipt(rows('Meal 6.99','Meal 6.99','TOTL 2.43','CASH 30.58','CHNG 40.00'))['amount_minor'] is None
    assert parse_receipt(rows('Meal 10.00','Discount 9.00','TOTAL 1.00'))['amount_minor']==100
    assert parse_receipt(rows('Meal 10.00','Receipt Total 5.00'))['amount_minor']==500


def test_dollar_decimal_comma_and_generic_service_item():
    result=parse_receipt(rows('City, State ZIP','Sandwich $8.99','Fries $3,49','Drink $2.29','Subtotal $14.77','Tax $1,26','Total $16,03'))
    assert result['amount_minor']==1603
    assert len(result['line_items'])==3
    assert result['merchant'] is None
    result=parse_receipt(rows('Transaction:123456','Product/Service $24.99','Additional Item $15.99','Subtotal $40.98','Tax $3.48','Total $44.46'))
    assert result['amount_minor']==4446 and len(result['line_items'])==2
    assert result['merchant'] is None
    assert parse_receipt(rows('Total $1,234.56'))['amount_minor']==123456
    assert parse_receipt(rows('Total 16,03'))['amount_minor'] is None
    assert parse_receipt(rows('Total $16,03','Total $17.03'))['amount_minor'] is None
