from stablevoy.errors.api_error import ApiError


class ValidationError(ApiError):
    """The request was refused because of its content (HTTP 400 or 422); issues names the fields."""
