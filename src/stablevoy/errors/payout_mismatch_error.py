from stablevoy.errors.stablevoy_error import StablevoyError


class PayoutMismatchError(StablevoyError):
    """No network of the new invoice pays to a wallet the shop confirmed: the payment page would show nothing payable. Do
    not send the buyer to it; tell the merchant to confirm the new wallet in the shop, or to check the store if they changed
    nothing. The message names the confirmed and the invoice wallets."""
