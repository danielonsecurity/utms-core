import logging
import sys
import tempfile
from pathlib import Path
from typing import Tuple
from logging.handlers import RotatingFileHandler
import os

def create_console_handler(level: int) -> logging.Handler:
    """Create console handler with basic formatting."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(levelname)s: %(message)s")
    )
    handler.setLevel(level)
    return handler

def create_temp_file_handler(level: int) -> Tuple[logging.Handler, Path]:
    """Create temporary file handler for bootstrap logging."""
    # Create temporary file
    temp_fd, temp_path = tempfile.mkstemp(
        prefix='utms_bootstrap_',
        suffix='.log'
    )
    temp_file = Path(temp_path)
    
    # Close file descriptor (file will be managed by handler)
    
    os.close(temp_fd)
    
    handler = logging.FileHandler(temp_file)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    handler.setLevel(level)
    
    # Test write to temp file
    with open(temp_file, 'w') as f:
        f.write("=== Bootstrap Log Started ===\n")

    return handler, temp_file

def create_rotating_handler(log_file: Path, level: int) -> logging.Handler:
    """Create rotating file handler for main logging."""
    
    
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    handler.setLevel(level)
    
    return handler

