import pytest
from pigpen.domain import all_approved, due_date, month_bounds, previous_month
from pigpen.errors import DomainError


@pytest.mark.parametrize('month,day,expected',[('2024-02',31,'2024-02-29'),('2026-02',31,'2026-02-28'),('2026-04',31,'2026-04-30')])
def test_short_months(month,day,expected):
    assert due_date(month,day)==expected


def test_calendar_and_unanimity():
    assert previous_month('2026-01')=='2025-12'
    assert month_bounds('2026-11')==('2026-11-01','2026-11-30')
    assert not all_approved('a',['a'],[],1)
    votes=[dict(reviewer_id=x,approved=True,request_revision=1) for x in ['b','c']]
    assert all_approved('a',['a','b','c'],votes,1)
    assert not all_approved('a',['a','b','c'],votes,2)


@pytest.mark.parametrize('month',['2026-00','2026-13','2026-1','not-a-month'])
def test_invalid_calendar_months(month):
    with pytest.raises(DomainError):month_bounds(month)
