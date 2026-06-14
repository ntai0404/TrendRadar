"""
Custom error class

Define all custom exception types used by MCP Server.
"""

from typing import Optional, List, Callable


# ==================== List of supported platforms for lazy loading ====================

_get_supported_platforms: Optional[Callable[[], List[str]]] = None


def _load_supported_platforms() -> List[str]:
    """Lazy loading supported platform list"""
    global _get_supported_platforms
    if _get_supported_platforms is None:
        try:
            from .validators import get_supported_platforms
            _get_supported_platforms = get_supported_platforms
        except ImportError:
            # Downgrade: return empty list
            return []
    return _get_supported_platforms()


class MCPError(Exception):
    """MCP Tool Error Base Class"""

    def __init__(self, message: str, code: str = "MCP_ERROR", suggestion: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.suggestion = suggestion

    def to_dict(self) -> dict:
        """Convert to dictionary format"""
        error_dict = {
            "code": self.code,
            "message": self.message
        }
        if self.suggestion:
            error_dict["suggestion"] = self.suggestion
        return error_dict


class DataNotFoundError(MCPError):
    """There is no error in the data"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="DATA_NOT_FOUND",
            suggestion=suggestion or "Please check the date range or wait for the crawl task to complete"
        )


class InvalidParameterError(MCPError):
    """Invalid parameter error"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="INVALID_PARAMETER",
            suggestion=suggestion or "Please check whether the parameter format is correct"
        )


class ConfigurationError(MCPError):
    """Configuration error"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            suggestion=suggestion or "Please check whether the configuration file is correct"
        )


class PlatformNotSupportedError(MCPError):
    """Platform not supported error"""

    def __init__(self, platform: str):
        supported = _load_supported_platforms()
        suggestion = f"Supported platforms: {', '.join(supported)}" if supported else "Please check the platform configuration in config/config.yaml"
        super().__init__(
            message=f"Platform '{platform}' is not supported",
            code="PLATFORM_NOT_SUPPORTED",
            suggestion=suggestion
        )


class CrawlTaskError(MCPError):
    """Crawling task error"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="CRAWL_TASK_ERROR",
            suggestion=suggestion or "Please try again later or check the log"
        )


class FileParseError(MCPError):
    """File parsing error"""

    def __init__(self, file_path: str, reason: str):
        super().__init__(
            message=f"Failed to parse file {file_path}: {reason}",
            code="FILE_PARSE_ERROR",
            suggestion="Please check whether the file format is correct"
        )
