"""Framework-free rules. No FastAPI, ORM or storage imports."""
from calendar import monthrange
from datetime import date
from .errors import DomainError

MAX_MINOR = 9_000_000_000_000


def month_bounds(month):
    try:
        if len(month) != 7:
            raise ValueError()
        year, n = map(int, month.split('-'))
        first = date(year, n, 1)
        if first.strftime('%Y-%m') != month or year < 1900 or year > 9998:
            raise ValueError()
        return first.isoformat(), date(year, n, monthrange(year, n)[1]).isoformat()
    except (ValueError, TypeError):
        raise DomainError('month', 'Use a calendar month in YYYY-MM format (1900–9998)')


def previous_month(month):
    month_bounds(month)
    year, n = map(int, month.split('-'))
    return f'{year-1:04d}-12' if n == 1 else f'{year:04d}-{n-1:02d}'


def due_date(month, day):
    first, _ = month_bounds(month)
    year, n = map(int, month.split('-'))
    return date(year, n, min(day, monthrange(year, n)[1])).isoformat()


def all_approved(requester_id, active_ids, votes, request_revision):
    eligible = set(active_ids) - {requester_id}
    approvals = {v['reviewer_id'] for v in votes if v['approved'] and v['request_revision'] == request_revision}
    return bool(eligible) and eligible <= approvals
