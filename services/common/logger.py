import logging
import sys
from pathlib import Path
import os


def setup_logger(name: str, level: str = None):
    """Setup logger with consistent formatting"""
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO')
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if logs directory exists
    logs_dir = Path(os.getenv('LOGS_DIR', '/pipeline-data/logs'))
    if logs_dir.exists():
        file_handler = logging.FileHandler(logs_dir / f'{name}.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
