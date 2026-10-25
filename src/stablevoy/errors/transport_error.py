from stablevoy.errors.stablevoy_error import StablevoyError


class TransportError(StablevoyError):
    """No answer from the API: the connection failed or timed out."""
