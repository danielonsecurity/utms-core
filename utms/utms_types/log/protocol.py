# utms_types/logging/protocols.py
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Protocol, Union


class LogProvider(Protocol):
    """Protocol for consistent logging interface."""

    def get_logger(self, name: str, level: Optional[Union[int, str]] = None) -> logging.Logger:
        """Get or create a logger with the specified name.

        Args:
            name: Logger name
            level: Optional logging level

        Returns:
            Configured logger instance
        """
        ...

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure logging system.

        Args:
            config: Configuration dictionary
        """
        ...

    def set_level(self, level: Union[int, str], logger_name: Optional[str] = None) -> None:
        """Set logging level for specified or root logger.

        Args:
            level: Logging level
            logger_name: Optional logger name (root logger if None)
        """
        ...

    def add_file_handler(
        self,
        file_path: Union[str, Path],
        level: Optional[Union[int, str]] = None,
        format_str: Optional[str] = None,
        logger_name: Optional[str] = None,
    ) -> None:
        """Add file handler to logger.

        Args:
            file_path: Log file path
            level: Optional logging level
            format_str: Optional format string
            logger_name: Optional logger name (root logger if None)
        """
        ...

    def add_stream_handler(
        self,
        level: Optional[Union[int, str]] = None,
        format_str: Optional[str] = None,
        logger_name: Optional[str] = None,
    ) -> None:
        """Add stream handler to logger.

        Args:
            level: Optional logging level
            format_str: Optional format string
            logger_name: Optional logger name (root logger if None)
        """
        ...

    def set_formatter(self, format_str: str, logger_name: Optional[str] = None) -> None:
        """Set formatter for all handlers of specified logger.

        Args:
            format_str: Format string
            logger_name: Optional logger name (root logger if None)
        """
        ...

    def add_filter(
        self, filter_func: Callable[[logging.LogRecord], bool], logger_name: Optional[str] = None
    ) -> None:
        """Add filter to logger.

        Args:
            filter_func: Filter function
            logger_name: Optional logger name (root logger if None)
        """
        ...
