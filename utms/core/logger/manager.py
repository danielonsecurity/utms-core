import sys
import inspect
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional

from .handlers import create_console_handler, create_temp_file_handler, create_rotating_handler

class LoggerManager:
    """Centralized logger management with bootstrap and component-specific levels."""
    
    _initialized = False
    _loggers: Dict[str, logging.Logger] = {}
    _component_levels: Dict[str, int] = {}
    _default_level = logging.INFO
    
    # Handlers
    _console_handler = None
    _temp_file_handler = None
    _main_file_handler = None
    _temp_log_file: Optional[Path] = None
    
    @classmethod
    def bootstrap(cls, cli_level: Optional[str] = None) -> None:
        """Initialize bootstrap logging."""
        print("=== Bootstrap called ===")  # Debug

        if cls._initialized:
            print("Already initialized, skipping bootstrap")
            return

        # Check if already bootstrapped
        if cls._temp_file_handler:
            print(f"Already have temp handler: {cls._temp_file_handler}")
            return

        bootstrap_level_name = (
            cli_level or 
            os.environ.get('UTMS_LOG_LEVEL', 'INFO')
        ).upper()
        bootstrap_level = getattr(logging, bootstrap_level_name, logging.INFO)

        print(f"Creating handlers with level: {bootstrap_level_name}")  # Debug

        # Create handlers
        cls._console_handler = create_console_handler(bootstrap_level)
        cls._temp_file_handler, cls._temp_log_file = create_temp_file_handler(bootstrap_level)

        bootstrap_logger = cls.get_logger('bootstrap')
        bootstrap_logger.info("Bootstrap logging initialized")

        print(f"Created temp file: {cls._temp_log_file}")  # Debug
        print(f"Created temp handler: {cls._temp_file_handler}")  # Debug

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str = None) -> logging.Logger:
        """Get or create a logger with component-specific configuration.

        Args:
            name: Optional logger name. If None, uses caller's module name.
        """
        print(f"=== Get logger called for: {name} ===")  # Debug
        print(f"Current temp handler: {cls._temp_file_handler}")  # Debug
        if not cls._initialized:
            cls.bootstrap()
        if not name:
            # Get caller's module name
            frame = sys._getframe(1)

            while frame:
                package = frame.f_globals.get("__package__", "")
                if package and not (package.startswith("importlib") or package == "utms.core.logger"):
                    name = package
                    break
                frame = frame.f_back
                
            print(f"Getting logger for module: {name}")  # Temporary debug
            breakpoint()

        if name not in cls._loggers:
            logger = logging.getLogger(f"utms.{name}")

            # Add handlers if not already present
            if not logger.handlers:
                if cls._console_handler:
                    logger.addHandler(cls._console_handler)
                if cls._temp_file_handler:
                    logger.addHandler(cls._temp_file_handler)
                if cls._main_file_handler:
                    logger.addHandler(cls._main_file_handler)

            # Set level
            level = cls._component_levels.get(name, cls._default_level)
            logger.setLevel(level)

            cls._loggers[name] = logger

        return cls._loggers[name]




    @classmethod
    def configure_file_logging(cls, utms_dir: str) -> None:
        """Set up proper file logging once config dir is available."""
        print("=== Configure file logging called ===")  # Debug
        print(f"Temp handler before: {cls._temp_file_handler}")  # Debug
        print(f"Temp file before: {cls._temp_log_file}")  # Debug
        logs_dir = Path(utms_dir) / 'logs'
        logs_dir.mkdir(exist_ok=True)

        # Set up main log file
        log_file = logs_dir / 'utms.log'

        # Move bootstrap logs if they exist
        if cls._temp_log_file and cls._temp_log_file.exists():
            try:
                # Close and remove the temporary file handler first
                if cls._temp_file_handler:
                    cls._temp_file_handler.close()
                    for logger in cls._loggers.values():
                        if cls._temp_file_handler in logger.handlers:
                            logger.removeHandler(cls._temp_file_handler)

                # Now copy the content
                bootstrap_content = cls._temp_log_file.read_text()
                with open(log_file, 'a') as f:
                    f.write("\n=== Bootstrap Logs ===\n")
                    f.write(bootstrap_content)

                # Clean up
                cls._temp_log_file.unlink()
                cls._temp_file_handler = None
                cls._temp_log_file = None

            except Exception as e:
                # Get logger without using temp handler
                logger = logging.getLogger("utms.core.logger")
                logger.error(f"Failed to migrate bootstrap logs: {e}")

    @classmethod
    def configure_from_config(cls, config_level: str) -> None:
        """Update logging configuration from loaded config."""
        level = getattr(logging, config_level.upper(), logging.INFO)
        
        bootstrap_logger = cls.get_logger("bootstrap")
        bootstrap_logger.info("Updating logging configuration from config")
        
        cls._default_level = level
        
        # Update existing loggers
        for name, logger in cls._loggers.items():
            if name not in cls._component_levels:
                logger.setLevel(level)
                bootstrap_logger.debug(
                    "Updated logger level: %s -> %s", 
                    name, 
                    logging.getLevelName(level)
                )
        
        # Update handlers
        if cls._console_handler:
            cls._console_handler.setLevel(level)
        if cls._main_file_handler:
            cls._main_file_handler.setLevel(level)

    @classmethod
    def set_component_level(cls, component: str, level: int) -> None:
        """Set log level for specific component."""
        cls._component_levels[component] = level
        if component in cls._loggers:
            cls._loggers[component].setLevel(level)
            logger = cls.get_logger("logger")
            logger.debug(
                "Set component level: %s -> %s",
                component,
                logging.getLevelName(level)
            )
        
