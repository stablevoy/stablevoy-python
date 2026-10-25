from stablevoy.errors.stablevoy_error import StablevoyError


class SignatureError(StablevoyError):
    """A webhook did not pass the signature check; the message says why. Answer such a request with HTTP 400."""
