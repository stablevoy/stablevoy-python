from stablevoy.errors.stablevoy_error import StablevoyError


class ConfigurationError(StablevoyError):
    """The client cannot be built as asked, for example with an empty API key or an unsafe base URL."""
