import re

from stablevoy.model.summary_period import SummaryPeriod

_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")


def summary_range_query(period: str | None, created_from: str | None, created_to: str | None) -> dict[str, str | int]:
    """
    The query of a range of UTC days, as invoices.summary() and stores.checkout_funnel() take it: a period, or both
    days. Refused here when it is not one the API takes.
    """
    has_days = created_from is not None or created_to is not None
    if (period is not None) == has_days:
        raise ValueError("Pass either period or both created_from and created_to")
    query: dict[str, str | int] = {}
    if period is not None:
        if period not in SummaryPeriod.ALL:
            raise ValueError(f"period must be one of {', '.join(SummaryPeriod.ALL)}")
        query["period"] = period
        return query
    for name, key, day in (("created_from", "createdFrom", created_from), ("created_to", "createdTo", created_to)):
        if day is None or not _DAY.fullmatch(day):
            raise ValueError(f"{name} must be a date as YYYY-MM-DD")
        query[key] = day
    return query
