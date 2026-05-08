"""Centralized logging utility with structured formatting."""

import logging
import sys
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Create timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format: [TIMESTAMP] [LEVEL] [MODULE] message
        return f"{log_color}[{timestamp}] [{record.levelname}] [{record.module}]{reset_color} {record.getMessage()}"

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger with consistent formatting and stdout output."""
    
    logger = logging.getLogger(name)
    
    # Set level
    logger.setLevel(logging.INFO)
    
    # Create handler that outputs to stdout (for docker logs)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Set formatter
    formatter = ColoredFormatter()
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

# Create a default logger for the application
logger = setup_logger('redbus')
