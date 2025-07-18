"""
Logging utilities for DXT Curator.

This module provides structured logging that works well with both
CLI usage and programmatic usage.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None, 
                 include_timestamp: bool = True) -> logging.Logger:
    """
    Set up logging for DXT Curator.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        include_timestamp: Whether to include timestamps in log messages
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('dxt_curator')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatter
    if include_timestamp:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = 'dxt_curator') -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)