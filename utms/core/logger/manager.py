import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Union

from .handlers import create_console_handler, create_rotating_handler, create_temp_file_handler


class LoggerManager:
    """Centralized logger management with bootstrap and component-specific levels."""

    _initialized = False
    _loggers: Dict[str, logging.Logger] = {}
    _component_patterns: Dict[str, int] = {}
    _default_level = logging.INFO
    _log_file: Optional[Path] = None

    @classmethod
    def bootstrap(cls, cli_level: Optional[str] = None) -> None:
        """Initialize bootstrap logging."""
        if cls._initialized:
            return

        # Set bootstrap level from CLI or environment
        bootstrap_level_name = (cli_level or os.environ.get("UTMS_LOG_LEVEL", "INFO")).upper()
        bootstrap_level = getattr(logging, bootstrap_level_name, logging.INFO)
        cls._default_level = bootstrap_level

        # Create handlers first
        cls._console_handler = create_console_handler(bootstrap_level)
        cls._temp_file_handler, cls._temp_log_file = create_temp_file_handler(bootstrap_level)

        # Mark as initialized BEFORE getting logger
        cls._initialized = True

        # Now create bootstrap logger
        logger = logging.getLogger("utms.bootstrap")
        logger.setLevel(bootstrap_level)
        logger.addHandler(cls._console_handler)
        logger.addHandler(cls._temp_file_handler)
        cls._loggers["bootstrap"] = logger

        logger.info("Bootstrap logging initialized")

    @classmethod
    def get_logger(cls, name: str = None) -> logging.Logger:
        """Get or create a logger with component-specific configuration."""
        if not cls._initialized:
            cls.bootstrap()

        # Auto-detect module name if not provided
        if not name:
            frame = sys._getframe(1)
            while frame:
                module_name = frame.f_globals["__name__"]
                package = frame.f_globals.get("__package__", "")
                if package and not (
                    package.startswith("importlib") or package == "utms.core.logger"
                ):
                    name = module_name
                    break
                frame = frame.f_back

        # Remove utms prefix if present
        if name.startswith("utms."):
            name = name.replace("utms.", "", 1)

        # Get level from patterns
        level = cls._default_level
        for pattern, pattern_level in cls._component_patterns.items():
            if re.search(pattern, name):
                level = pattern_level
                break

        # Create new logger or update existing one
        if name not in cls._loggers:
            logger = logging.getLogger(f"utms.{name}")
            logger.setLevel(level)

            # Add handlers with correct level
            console_handler = create_console_handler(level)
            logger.addHandler(console_handler)

            if cls._log_file:
                file_handler = create_rotating_handler(cls._log_file, level)
                logger.addHandler(file_handler)

            cls._loggers[name] = logger
        else:
            # Update existing logger's handlers to correct level
            logger = cls._loggers[name]
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)

        return logger

    @classmethod
    def configure_file_logging(cls, utms_dir: str) -> None:
        """Set up proper file logging once config dir is available."""
        # Set up log directory
        logs_dir = Path(utms_dir) / "logs"
        logs_dir.mkdir(exist_ok=True)
        cls._log_file = logs_dir / "utms.log"

        # Migrate bootstrap logs if they exist
        if cls._temp_log_file and cls._temp_log_file.exists():
            try:
                bootstrap_content = cls._temp_log_file.read_text()

                # Close temp handler
                if cls._temp_file_handler:
                    cls._temp_file_handler.close()
                    for logger in cls._loggers.values():
                        if cls._temp_file_handler in logger.handlers:
                            logger.removeHandler(cls._temp_file_handler)

                # Write bootstrap logs to main log
                with open(cls._log_file, "a") as f:
                    f.write("\n=== Bootstrap Logs ===\n")
                    f.write(bootstrap_content)
                    f.write("=== End Bootstrap Logs ===\n\n")

                # Clean up temp file
                cls._temp_log_file.unlink()
            except Exception as e:
                print(f"Error migrating bootstrap logs: {e}")

        # Add file handlers to all loggers
        for name, logger in cls._loggers.items():
            # Get level from patterns
            level = cls._default_level
            for pattern, pattern_level in cls._component_patterns.items():
                if re.search(pattern, name):
                    level = pattern_level
                    break

            file_handler = create_rotating_handler(cls._log_file, level)
            logger.addHandler(file_handler)

        # Clean up bootstrap resources
        cls._temp_file_handler = None
        cls._temp_log_file = None

        # Log confirmation
        logger = cls.get_logger("core.logger")
        logger.info(f"File logging configured in {logs_dir}")

    @classmethod
    def configure_from_config(cls, config_level: Dict[str, str]) -> None:
        """Update logging configuration from loaded config."""
        level = getattr(logging, config_level.value.upper(), logging.INFO)
        cls._default_level = level

        # Update all loggers and their handlers
        for name, logger in cls._loggers.items():
            # Get level from patterns
            logger_level = cls._default_level
            for pattern, pattern_level in cls._component_patterns.items():
                if re.search(pattern, name):
                    logger_level = pattern_level
                    break

            logger.setLevel(logger_level)
            for handler in logger.handlers:
                handler.setLevel(logger_level)

        bootstrap_logger = cls.get_logger("bootstrap")
        bootstrap_logger.info("Updated logging configuration from config")

    @classmethod
    def set_component_pattern(cls, pattern: str, level: Union[str, int]) -> None:
        """Set log level for components matching pattern."""
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        cls._component_patterns[pattern] = level

        # Update existing loggers that match the pattern
        for name, logger in cls._loggers.items():
            if re.search(pattern, name):
                logger.setLevel(level)
                for handler in logger.handlers:
                    handler.setLevel(level)

        logger = cls.get_logger("core.logger")
        logger.info(
            f"Set log level to {logging.getLevelName(level)} for components matching '{pattern}'"
        )

    @classmethod
    def get_component_levels(cls) -> Dict[str, str]:
        """Get current component patterns and their levels."""
        return {
            pattern: logging.getLevelName(level)
            for pattern, level in cls._component_patterns.items()
        }

    @classmethod
    def reset_component_level(cls, pattern: str) -> None:
        """Reset components matching pattern to default level."""
        if pattern in cls._component_patterns:
            del cls._component_patterns[pattern]

            # Reset matching loggers to default
            for name, logger in cls._loggers.items():
                if re.search(pattern, name):
                    logger.setLevel(cls._default_level)
                    for handler in logger.handlers:
                        handler.setLevel(cls._default_level)

        logger = cls.get_logger("core.logger")
        logger.info(
            f"Reset components matching '{pattern}' to default ({logging.getLevelName(cls._default_level)})"
        )
