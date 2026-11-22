from typing import Final


class CheckoutSurface:
    """Where the payment page ran when it was opened: the hosted page or the widget on the store's site."""

    PAGE: Final = "page"
    WIDGET: Final = "widget"
