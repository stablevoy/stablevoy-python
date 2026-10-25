from stablevoy.errors.api_error import ApiError


class MaintenanceError(ApiError):
    """Stablevoy is under maintenance (HTTP 503, code maintenance). Nothing was changed; retry after retry_after_seconds."""
