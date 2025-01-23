import logging
import sys

# Create logger
logger = logging.getLogger("utms")
logger.setLevel(logging.DEBUG)

# Create console handler with a higher log level
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# Create file handler which logs even debug messages
file_handler = logging.FileHandler("/tmp/utms.log")
file_handler.setLevel(logging.DEBUG)

# Create formatters and add it to the handlers
console_format = logging.Formatter("%(levelname)s: %(message)s")
file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

console_handler.setFormatter(console_format)
file_handler.setFormatter(file_format)

# Add the handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(f"utms.{name}")


def set_log_level(level):
    """Set the log level for both console and file handlers.

    Args:
        level: Can be logging.DEBUG, logging.INFO, logging.WARNING,
              logging.ERROR, logging.CRITICAL
              or 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    """
    logger = logging.getLogger("utms")

    # Convert string to logging level if necessary
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
