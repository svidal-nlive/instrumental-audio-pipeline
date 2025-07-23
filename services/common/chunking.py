"""
Basic chunking utilities for processing large audio files
"""
import os
from pathlib import Path
from .logger import setup_logger

logger = setup_logger("chunking")


def process_with_chunking(func, input_file: Path, output_dir: Path, *args, **kwargs):
    """
    Process file with chunking support if enabled
    """
    enable_chunking = os.getenv('ENABLE_CHUNKING', 'false').lower() == 'true'
    
    if not enable_chunking:
        return func(input_file, output_dir, *args, **kwargs)
    
    # For now, just call the function directly
    # Real chunking implementation would go here
    logger.info(f"Processing {input_file} (chunking enabled but not implemented)")
    return func(input_file, output_dir, *args, **kwargs)


def is_oom_error(error):
    """Check if error is out of memory"""
    error_str = str(error).lower()
    return any(keyword in error_str for keyword in ['out of memory', 'oom', 'memory'])


def get_chunk_duration():
    """Get chunk duration from environment"""
    return int(os.getenv('CHUNK_DURATION_SEC', '300'))  # 5 minutes default
