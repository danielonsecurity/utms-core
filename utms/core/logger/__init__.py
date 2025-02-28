import logging
from .manager import LoggerManager

def get_logger(name: str = None) -> logging.Logger:
    return LoggerManager.get_logger(name)
