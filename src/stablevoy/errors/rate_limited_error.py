from stablevoy.errors.api_error import ApiError


class RateLimitedError(ApiError):
    """Too many requests (HTTP 429); retry_after_seconds says when to try again."""
