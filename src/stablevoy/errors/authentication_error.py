from stablevoy.errors.api_error import ApiError


class AuthenticationError(ApiError):
    """The API key is missing, invalid or revoked (HTTP 401)."""
