from stablevoy.errors.stablevoy_error import StablevoyError


class UnexpectedResponseError(StablevoyError):
    """The API answered something this library cannot read: not JSON, or a field missing or of the wrong type."""
