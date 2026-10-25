from stablevoy.errors.api_error import ApiError


class NotFoundError(ApiError):
    """The invoice or store does not exist for this API key (HTTP 404)."""
