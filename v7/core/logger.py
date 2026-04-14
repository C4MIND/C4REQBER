"""
TURBO-CDI v7.0 Logging System
Centralized logging configuration for all modules
"""

import logging
import sys
from pathlib import Path


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Setup a logger with both console and file handlers.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers if they already exist
    if logger.handlers:
        return logger
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # File handler
    log_dir = Path.home() / '.turbo-cdi' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / 'turbo-cdi.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
