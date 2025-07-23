"""
Processing tracker for managing job status
"""
import os
import json
from pathlib import Path
from .logger import setup_logger

logger = setup_logger("processing_tracker")


class ProcessingTracker:
    """Track processing status with marker files"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.getenv('PIPELINE_DATA_DIR', '/pipeline-data'))
    
    def create_marker(self, file_path: Path, status: str = 'processing'):
        """Create a processing marker file"""
        marker_file = file_path.with_suffix(f'.{status}')
        try:
            with open(marker_file, 'w') as f:
                json.dump({
                    'file': str(file_path),
                    'status': status,
                    'created_at': str(Path().ctime())
                }, f)
            logger.debug(f"Created marker: {marker_file}")
        except Exception as e:
            logger.error(f"Failed to create marker {marker_file}: {e}")
    
    def remove_marker(self, file_path: Path, status: str = 'processing'):
        """Remove a processing marker file"""
        marker_file = file_path.with_suffix(f'.{status}')
        try:
            if marker_file.exists():
                marker_file.unlink()
                logger.debug(f"Removed marker: {marker_file}")
        except Exception as e:
            logger.error(f"Failed to remove marker {marker_file}: {e}")
    
    def is_processing(self, file_path: Path) -> bool:
        """Check if file is currently being processed"""
        marker_file = file_path.with_suffix('.processing')
        return marker_file.exists()
