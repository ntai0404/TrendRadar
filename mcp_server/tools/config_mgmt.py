"""
Configuration management tools

Implement configuration query and management functions.
"""

from typing import Dict, Optional, Any, TypedDict

from ..services.data_service import DataService
from ..utils.validators import validate_config_section
from ..utils.errors import MCPError


class ErrorInfo(TypedDict, total=False):
    """Error message structure"""
    code: str
    message: str
    suggestion: str


class ConfigResult(TypedDict):
    """Configure query results - the success field is required, other fields are optional"""
    success: bool
    config: Optional[Dict[str, Any]]
    section: Optional[str]
    error: Optional[ErrorInfo]


class ConfigManagementTools:
    """Configuration management tool class"""

    def __init__(self, project_root: str = None):
        """
        Initialize configuration management tool

        Args:
            project_root: project root directory
        """
        self.data_service = DataService(project_root)

    def get_current_config(self, section: Optional[str] = None) -> ConfigResult:
        """
        Get current system configuration

        Args:
            section: Configuration section - all/crawler/push/keywords/weights, default all

        Returns:
            Configuration dictionary

        Example:
            >>> tools = ConfigManagementTools()
            >>> result = tools.get_current_config(section="crawler")
            >>> print(result['crawler']['platforms'])
        """
        try:
            # Parameter validation
            section = validate_config_section(section)

            # Get configuration
            config = self.data_service.get_current_config(section=section)

            return ConfigResult(
                success=True,
                config=config,
                section=section,
                error=None
            )

        except MCPError as e:
            return ConfigResult(
                success=False,
                config=None,
                section=None,
                error=e.to_dict()
            )
        except Exception as e:
            return ConfigResult(
                success=False,
                config=None,
                section=None,
                error={"code": "INTERNAL_ERROR", "message": str(e), "suggestion": "Please check the service log for details"}
            )
