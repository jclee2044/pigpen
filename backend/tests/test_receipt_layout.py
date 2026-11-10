from pigpen.receipt_layout import group_rows
from pigpen.receipt_parser import parse_receipt


def token(text,x,y,width=100,height=45):
    return dict(text=text,x=x,center_x=x+width/2,raw_y=y,width=width,height=height,slope=-.02,score=.99)


def test_slanted_prices_do_not_shift_into_next_summary_label():
    result=group_rows([token('Counter-Take Out',200,644,300),token('2.00',650,687),
        token('TAX 8.25%',200,720,200),token('.17',650,728),
        token('Amount Due',200,760,200),token('$2.17',650,769),
        token('Cash Tender',200,833,200),token('$3.00',650,849),
        token('Change',200,875,150),token('$.83',650,890),token('THANK YOU',300,908,250)])
    assert [r['text'] for r in result]==['Counter-Take Out 2.00','TAX 8.25% .17','Amount Due $2.17','Cash Tender $3.00','Change $.83','THANK YOU']
    assert parse_receipt(result)['amount_minor']==217


def test_unit_and_extended_prices_and_unpriced_modifiers():
    result=group_rows([token('2 Tea',0,100),token('2.00',200,100),token('4.00',400,100),
                      token('No sugar',0,150),token('TOTAL',0,200),token('4.00',400,200)])
    assert [r['text'] for r in result]==['2 Tea 2.00 4.00','No sugar','TOTAL 4.00']
    assert parse_receipt(result)['line_items']==[{'description':'2 Tea','line_total_minor':400}]
