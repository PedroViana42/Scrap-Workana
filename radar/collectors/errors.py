class CollectorError(Exception):
    """Base collector error."""


class CollectorConfigurationError(CollectorError):
    """Collector was called with invalid or missing configuration."""


class CollectorHTTPError(CollectorError):
    """Source returned an HTTP error or could not be reached."""


class CollectorParseError(CollectorError):
    """Source response could not be parsed into domain objects."""

