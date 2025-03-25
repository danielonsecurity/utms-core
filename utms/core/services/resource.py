import importlib.resources
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from utms.core.mixins import ServiceMixin


class ResourceService(ServiceMixin):
    """Service for managing system resource files.

    Currently handles basic resource deployment and tracking,
    structured for future expansion into version control and backups.
    """

    DEFAULT_RESOURCES = [
        "anchors.hy",
        "calendar_units.hy",
        "config.hy",
        "fixed_units.hy",
        "patterns.hy",
        "system_prompt.txt",
        "events.hy",
        "variables.hy",
    ]

    def __init__(self, config_dir: str):
        self._config_dir = Path(config_dir)
        self._resource_status: Dict[str, bool] = {}

    def init_resources(self, force: bool = False) -> None:
        """Initialize all default resources in the config directory."""
        self.logger.debug("Initializing resources in %s", self._config_dir)

        for resource in self.DEFAULT_RESOURCES:
            self.deploy_resource(resource, force)

    def deploy_resource(self, resource_name: str, force: bool = False) -> bool:
        """Deploy a single resource file.

        Args:
            resource_name: Name of the resource file
            force: If True, overwrite existing file

        Returns:
            bool: True if resource was deployed, False if already exists
        """
        destination = self._config_dir / resource_name

        if destination.exists() and not force:
            self.logger.debug("Resource %s already exists", resource_name)
            self._resource_status[resource_name] = True
            return False

        try:
            source = importlib.resources.files("utms.resources") / resource_name
            shutil.copy(str(source), str(destination))
            self.logger.info("Deployed resource %s to %s", resource_name, destination)
            self._resource_status[resource_name] = True
            return True
        except Exception as e:
            self.logger.error("Failed to deploy resource %s: %s", resource_name, e)
            self._resource_status[resource_name] = False
            raise

    def get_resource_path(self, resource_name: str) -> Optional[Path]:
        """Get the full path to a resource file.

        Args:
            resource_name: Name of the resource file

        Returns:
            Optional[Path]: Full path to resource or None if not found
        """
        path = self._config_dir / resource_name
        return path if path.exists() else None

    def check_resource(self, resource_name: str) -> bool:
        """Check if a resource file exists.

        Args:
            resource_name: Name of the resource file

        Returns:
            bool: True if resource exists
        """
        return (self._config_dir / resource_name).exists()

    def get_status(self) -> Dict[str, bool]:
        """Get deployment status of all resources.

        Returns:
            Dict[str, bool]: Mapping of resource names to their status
        """
        return dict(self._resource_status)
