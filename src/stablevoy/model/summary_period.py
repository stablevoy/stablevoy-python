from typing import Final


class SummaryPeriod:
    """The ready-made ranges of invoices.summary(): UTC days ending today; LAST_3_MONTHS is the last 92 days."""

    LAST_7_DAYS: Final = "last_7_days"
    LAST_30_DAYS: Final = "last_30_days"
    THIS_MONTH: Final = "this_month"
    LAST_MONTH: Final = "last_month"
    LAST_3_MONTHS: Final = "last_3_months"

    ALL: Final = (LAST_7_DAYS, LAST_30_DAYS, THIS_MONTH, LAST_MONTH, LAST_3_MONTHS)
