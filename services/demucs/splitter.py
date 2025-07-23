"""
Basic Demucs splitter service
"""
import os
import time
import sys
from pathlib import Path

# Add common utilities to path
sys.path.append('/app/common')

from dotenv import load_dotenv
from common.logger import setup_logger

load_dotenv()
logger = setup_logger("demucs")

# Config
INPUT_DIR = Path("/pipeline-data/demucs-input")
OUTPUT_DIR = Path("/pipeline-data/output")

# Audio file extensions
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}


def find_audio_files(directory: Path):
    """Find audio files in directory"""
    if not directory.exists():
        return []
    
    files = []
    for file in directory.rglob("*"):
        if file.is_file() and file.suffix.lower() in ALLOWED_EXTENSIONS:
            files.append(file)
    return files


def process_file(file_path: Path):
    """Process a single audio file"""
    logger.info(f"Processing file: {file_path}")
    
    try:
        # For now, just copy the file to output (placeholder)
        output_file = OUTPUT_DIR / f"{file_path.stem}_instrumental.mp3"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # In real implementation, this would use Demucs
        import shutil
        shutil.copy2(file_path, output_file)
        
        logger.info(f"Processed: {file_path} -> {output_file}")
        
        # Remove input file
        file_path.unlink()
        
    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}")


def main():
    """Main processing loop"""
    logger.info("Starting Demucs splitter service...")
    
    # Create directories
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Watching input directory: {INPUT_DIR}")
    
    while True:
        try:
            # Find audio files to process
            audio_files = find_audio_files(INPUT_DIR)
            
            for file_path in audio_files:
                process_file(file_path)
            
            # Wait before checking again
            time.sleep(5)
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
