# utms_types/logging/protocols.py
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Protocol, Union


class LogProvider(Protocol):
    """Protocol for consistent logging interface."""

    def get_logger(self, name: str, level: Optional[Union[int, str]] = None) -> logging.Logger: ...

    def configure(self, config: Dict[str, Any]) -> None: ...

    def set_level(self, level: Union[int, str], logger_name: Optional[str] = None) -> None: ...

    def add_file_handler(
        self,
        file_path: Union[str, Path],
        level: Optional[Union[int, str]] = None,
        format_str: Optional[str] = None,
        logger_name: Optional[str] = None,
    ) -> None: ...

    def add_stream_handler(
        self,
        level: Optional[Union[int, str]] = None,
        format_str: Optional[str] = None,
        logger_name: Optional[str] = None,
    ) -> None: ...

    def set_formatter(self, format_str: str, logger_name: Optional[str] = None) -> None: ...

    def add_filter(
        self, filter_func: Callable[[logging.LogRecord], bool], logger_name: Optional[str] = None
    ) -> None: ...
