#!/usr/bin/env python3
"""
Music Library Organization Service

Handles organizing finalized music files into a structured library:
- Artist/Album/Song_Title.mp3 structure
- Metadata-based organization
- NFO file generation for media servers
- Filename sanitization
"""

import os
import sys
import logging
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Union
import asyncio
import aiofiles
import shutil

from mutagen import File as MutagenFile
from unidecode import unidecode

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FilenamesSanitizer:
    """Handles filename and path sanitization for cross-platform compatibility"""
    
    # Characters that are problematic in filenames
    FORBIDDEN_CHARS = r'[<>:"/\\|?*]'
    
    @staticmethod
    def sanitize(text: str, max_length: int = 200) -> str:
        """Sanitize text for use in filenames and paths"""
        if not text:
            return "Unknown"
        
        # Convert unicode to ASCII equivalents
        text = unidecode(text)
        
        # Remove or replace forbidden characters
        text = re.sub(FilenamesSanitizer.FORBIDDEN_CHARS, '_', text)
        
        # Remove multiple consecutive spaces/underscores
        text = re.sub(r'[\s_]+', ' ', text)
        
        # Trim whitespace
        text = text.strip()
        
        # Ensure reasonable length
        if len(text) > max_length:
            text = text[:max_length].strip()
        
        # Ensure not empty
        if not text:
            text = "Unknown"
            
        return text


class MusicLibraryOrganizer:
    """Main service for organizing music library"""
    
    def __init__(self, 
                 input_dir: Union[str, Path] = None,
                 library_dir: Union[str, Path] = None):
        # Use absolute paths relative to project root
        self.input_dir = Path(input_dir) if input_dir else PROJECT_ROOT / "data" / "output"
        self.library_dir = Path(library_dir) if library_dir else PROJECT_ROOT / "data" / "music-library"
        
        # Create library directory
        self.library_dir.mkdir(parents=True, exist_ok=True)
        
        self.sanitizer = FilenamesSanitizer()
    
    def extract_metadata(self, file_path: Union[str, Path]) -> Dict[str, str]:
        """Extract metadata from audio file for organization"""
        metadata = {
            'artist': 'Unknown Artist',
            'albumartist': None,
            'album': 'Unknown Album', 
            'title': None,
            'track': None,
            'disc': None
        }
        
        try:
            audio_file = MutagenFile(str(file_path))
            if audio_file is None:
                return metadata
            
            # Common metadata mappings
            tag_mappings = {
                'title': ['TIT2', 'TITLE', '\xa9nam'],
                'artist': ['TPE1', 'ARTIST', '\xa9ART'],
                'albumartist': ['TPE2', 'ALBUMARTIST', 'aART'],
                'album': ['TALB', 'ALBUM', '\xa9alb'],
                'track': ['TRCK', 'TRACKNUMBER', 'trkn'],
                'disc': ['TPOS', 'DISCNUMBER', 'disk'],
            }
            
            for key, tags in tag_mappings.items():
                for tag in tags:
                    if tag in audio_file:
                        value = audio_file[tag]
                        if isinstance(value, list) and value:
                            metadata[key] = str(value[0])
                        else:
                            metadata[key] = str(value)
                        break
            
            # Use filename as title if not found
            if not metadata.get('title'):
                metadata['title'] = Path(file_path).stem
            
            # Use artist as albumartist if not specified
            if not metadata.get('albumartist'):
                metadata['albumartist'] = metadata['artist']
                
            # Clean up track numbers (remove "/total" part if present)
            if metadata.get('track') and '/' in metadata['track']:
                metadata['track'] = metadata['track'].split('/')[0]
                
            logger.info(f"Extracted metadata: {metadata}")
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from {file_path}: {e}")
            metadata['title'] = Path(file_path).stem
            return metadata
    
    def generate_library_path(self, metadata: Dict[str, str], file_extension: str = '.mp3') -> Path:
        """Generate organized library path from metadata"""
        
        # Sanitize metadata
        artist = self.sanitizer.sanitize(metadata.get('albumartist') or metadata.get('artist', 'Unknown Artist'))
        album = self.sanitizer.sanitize(metadata.get('album', 'Unknown Album'))
        title = self.sanitizer.sanitize(metadata.get('title', 'Unknown Title'))
        
        # Add track number prefix if available
        track = metadata.get('track')
        if track and track.isdigit():
            track_num = int(track)
            title = f"{track_num:02d} - {title}"
        
        # Build path: Artist/Album/Song_Title.mp3
        library_path = self.library_dir / artist / album / f"{title}{file_extension}"
        
        logger.info(f"Generated library path: {library_path}")
        return library_path
    
    def move_to_library(self, source_file: Path, target_path: Path) -> bool:
        """Move file to library location, creating directories as needed"""
        try:
            # Create target directory
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle filename conflicts
            if target_path.exists():
                counter = 1
                base_name = target_path.stem
                extension = target_path.suffix
                parent = target_path.parent
                
                while target_path.exists():
                    new_name = f"{base_name} ({counter}){extension}"
                    target_path = parent / new_name
                    counter += 1
                
                logger.info(f"Renamed to avoid conflict: {target_path}")
            
            # Move the file
            shutil.move(str(source_file), str(target_path))
            logger.info(f"Moved {source_file} to {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving {source_file} to {target_path}: {e}")
            return False
    
    def create_artist_structure(self, artist_dir: Path) -> None:
        """Create additional structure for media servers if needed"""
        try:
            # Some media servers benefit from having these files
            artist_info_file = artist_dir / "artist.nfo"
            if not artist_info_file.exists():
                # Create a basic artist info file
                artist_name = artist_dir.name
                nfo_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<artist>
    <name>{artist_name}</name>
    <musicbrainzartistid></musicbrainzartistid>
    <biography></biography>
</artist>"""
                try:
                    with open(artist_info_file, 'w', encoding='utf-8') as f:
                        f.write(nfo_content)
                except Exception as e:
                    logger.warning(f"Could not create artist.nfo: {e}")
                    
        except Exception as e:
            logger.warning(f"Error creating artist structure: {e}")
    
    async def process_file(self, source_file: Path) -> bool:
        """Process a single file for library organization"""
        try:
            logger.info(f"Processing file for library organization: {source_file}")
            
            # Skip non-audio files
            if source_file.suffix.lower() not in ['.mp3', '.flac', '.m4a', '.wav']:
                logger.info(f"Skipping non-audio file: {source_file}")
                return False
            
            # Extract metadata
            metadata = self.extract_metadata(source_file)
            
            # Generate target path
            target_path = self.generate_library_path(metadata, source_file.suffix)
            
            # Move to library
            if not self.move_to_library(source_file, target_path):
                return False
            
            # Create artist structure for media servers
            self.create_artist_structure(target_path.parent.parent)
            
            logger.info(f"Successfully organized {source_file} to library")
            return True
            
        except Exception as e:
            logger.error(f"Error processing file {source_file}: {e}")
            return False
    
    async def scan_and_organize_existing(self) -> None:
        """Scan input directory and organize any existing files on startup"""
        try:
            logger.info(f"Scanning for existing files to organize in {self.input_dir}")
            
            if not self.input_dir.exists():
                logger.info(f"Input directory {self.input_dir} does not exist yet")
                return
            
            # Find all audio files in input directory
            audio_extensions = ['.mp3', '.flac', '.m4a', '.wav']
            audio_files = []
            
            for ext in audio_extensions:
                audio_files.extend(self.input_dir.rglob(f'*{ext}'))
                audio_files.extend(self.input_dir.rglob(f'*{ext.upper()}'))
            
            if audio_files:
                logger.info(f"Found {len(audio_files)} existing audio files to organize")
                
                organized_count = 0
                for audio_file in audio_files:
                    if await self.process_file(audio_file):
                        organized_count += 1
                
                logger.info(f"Organized {organized_count}/{len(audio_files)} existing files")
            else:
                logger.info("No existing audio files found to organize")
                
        except Exception as e:
            logger.error(f"Error scanning and organizing existing files: {e}")

    async def process_job(self, job_config: Dict) -> bool:
        """Process an organization job"""
        try:
            job_id = job_config.get('job_id')
            source_files = [Path(p) for p in job_config.get('source_files', [])]
            
            logger.info(f"Processing organization job {job_id} with {len(source_files)} files")
            
            success_count = 0
            for source_file in source_files:
                if source_file.exists():
                    if await self.process_file(source_file):
                        success_count += 1
                else:
                    logger.warning(f"Source file does not exist: {source_file}")
            
            logger.info(f"Job {job_id} completed: {success_count}/{len(source_files)} files organized")
            print(f"ORGANIZED_TO:{self.library_dir}")  # For backend to capture
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error processing organization job: {e}")
            return False


async def process_single_job(config_file: Path):
    """Process a single organization job from config file"""
    try:
        with open(config_file, 'r') as f:
            job_config = json.load(f)
        
        organizer = MusicLibraryOrganizer()
        success = await organizer.process_job(job_config)
        
        if success:
            logger.info("Single organization job completed successfully")
            return True
        else:
            logger.error("Single organization job failed")
            return False
            
    except Exception as e:
        logger.error(f"Error processing single organization job: {e}")
        return False


async def main():
    """Main service loop"""
    import sys
    
    # Check if we have a config file argument for single job processing
    if len(sys.argv) > 1:
        config_file = Path(sys.argv[1])
        if config_file.exists():
            success = await process_single_job(config_file)
            sys.exit(0 if success else 1)
        else:
            logger.error(f"Config file not found: {config_file}")
            sys.exit(1)
    
    # Service mode - continuous job processing
    organizer = MusicLibraryOrganizer()
    
    logger.info("Music Library Organization Service started")
    
    # Monitor for job files
    jobs_dir = PROJECT_ROOT / "data" / "jobs" / "organization"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    
    # Organize any existing files on startup
    await organizer.scan_and_organize_existing()
    
    while True:
        try:
            # Look for job files
            for job_file in jobs_dir.glob("*.json"):
                try:
                    async with aiofiles.open(job_file, 'r') as f:
                        job_config = json.loads(await f.read())
                    
                    success = await organizer.process_job(job_config)
                    
                    # Move job file to completed or failed
                    status_dir = jobs_dir.parent / ("completed" if success else "failed")
                    status_dir.mkdir(parents=True, exist_ok=True)
                    job_file.rename(status_dir / job_file.name)
                    
                except Exception as e:
                    logger.error(f"Error processing job file {job_file}: {e}")
            
            # Also monitor output directory for new files
            output_dir = PROJECT_ROOT / "data" / "output"
            for file_path in output_dir.rglob('*.mp3'):
                if file_path.is_file():
                    await organizer.process_file(file_path)
            
            await asyncio.sleep(5)  # Check every 5 seconds
            
        except KeyboardInterrupt:
            logger.info("Music Library Organization Service stopped")
            break
        except Exception as e:
            logger.error(f"Service error: {e}")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
