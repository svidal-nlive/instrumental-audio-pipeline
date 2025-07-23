#!/usr/bin/env python3
"""
Audio Reconstruction Service

Handles:
1. Recombining selected stems into final MP3
2. Extracting and applying metadata from original files
3. Cover art extraction and embedding
4. Smart cover art detection from folders
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Union
import asyncio
import aiofiles

from pydub import AudioSegment
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TPE1, TIT2, TALB, TDRC, TCON, TPE2
from mutagen import File as MutagenFile
import eyed3
from PIL import Image
import soundfile as sf

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoverArtExtractor:
    """Handles cover art extraction and processing"""
    
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    COMMON_COVER_NAMES = [
        'cover', 'folder', 'album', 'albumart', 'albumartsmall',
        'front', 'artwork', 'art', 'thumb', 'thumbnail'
    ]
    
    def extract_from_audio(self, file_path: Union[str, Path]) -> Optional[bytes]:
        """Extract embedded cover art from audio file"""
        try:
            audio_file = MutagenFile(str(file_path))
            if audio_file is None:
                return None
                
            # Handle MP3 files
            if hasattr(audio_file, 'tags') and audio_file.tags:
                for tag in audio_file.tags.values():
                    if hasattr(tag, 'type') and tag.type == 3:  # Front cover
                        return tag.data
                    elif hasattr(tag, 'data'):
                        return tag.data
                        
            # Handle other formats with mutagen
            if 'APIC:' in audio_file:
                return audio_file['APIC:'].data
                
            logger.info(f"No embedded cover art found in {file_path}")
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting cover art from {file_path}: {e}")
            return None
    
    def find_folder_cover_art(self, folder_path: Union[str, Path]) -> Optional[Path]:
        """Find cover art in the same folder as the audio file"""
        folder = Path(folder_path)
        
        # Look for common cover art filenames
        for name in self.COMMON_COVER_NAMES:
            for ext in self.SUPPORTED_IMAGE_FORMATS:
                cover_file = folder / f"{name}{ext}"
                if cover_file.exists():
                    logger.info(f"Found folder cover art: {cover_file}")
                    return cover_file
        
        # Look for any image file if no common names found
        for ext in self.SUPPORTED_IMAGE_FORMATS:
            image_files = list(folder.glob(f"*{ext}"))
            if image_files:
                logger.info(f"Found image file for cover art: {image_files[0]}")
                return image_files[0]
                
        logger.info(f"No cover art found in folder {folder}")
        return None
    
    def process_cover_art(self, cover_data: bytes, max_size: tuple = (800, 800)) -> bytes:
        """Process cover art to optimize size and format"""
        try:
            import io
            # Open image from bytes
            image = Image.open(io.BytesIO(cover_data))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Resize if too large
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save back to bytes
            import io
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=90)
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Error processing cover art: {e}")
            return cover_data


class MetadataExtractor:
    """Handles metadata extraction from audio files"""
    
    def extract_metadata(self, file_path: Union[str, Path]) -> Dict[str, str]:
        """Extract metadata from audio file"""
        metadata = {}
        
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
                'date': ['TDRC', 'DATE', '\xa9day'],
                'year': ['TDRC', 'DATE', '\xa9day'],
                'genre': ['TCON', 'GENRE', '\xa9gen'],
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
            
            # Extract filename-based metadata if not found
            if not metadata.get('title'):
                metadata['title'] = Path(file_path).stem
                
            logger.info(f"Extracted metadata from {file_path}: {metadata}")
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from {file_path}: {e}")
            return {'title': Path(file_path).stem}


class AudioReconstructor:
    """Main service for audio reconstruction"""
    
    def __init__(self, 
                 input_dir: Union[str, Path] = "data/output",
                 output_dir: Union[str, Path] = "data/output",
                 temp_dir: Union[str, Path] = "data/temp"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        
        self.cover_extractor = CoverArtExtractor()
        self.metadata_extractor = MetadataExtractor()
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def combine_stems(self, stems: List[Path], output_path: Path) -> bool:
        """Combine multiple stem files into a single audio file"""
        try:
            if not stems:
                logger.error("No stems provided for combination")
                return False
            
            logger.info(f"Combining {len(stems)} stems into {output_path}")
            
            # Load first stem as base
            combined = AudioSegment.from_file(str(stems[0]))
            
            # Overlay additional stems
            for stem_path in stems[1:]:
                try:
                    stem = AudioSegment.from_file(str(stem_path))
                    # Ensure same length
                    min_length = min(len(combined), len(stem))
                    combined = combined[:min_length].overlay(stem[:min_length])
                except Exception as e:
                    logger.warning(f"Error adding stem {stem_path}: {e}")
                    continue
            
            # Export as MP3
            combined.export(str(output_path), format="mp3", bitrate="320k")
            logger.info(f"Successfully combined stems to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error combining stems: {e}")
            return False
    
    def apply_metadata(self, audio_path: Path, metadata: Dict[str, str], 
                      cover_art_data: Optional[bytes] = None) -> bool:
        """Apply metadata and cover art to audio file"""
        try:
            # Load the audio file
            audio_file = MP3(str(audio_path), ID3=ID3)
            
            # Add ID3 tags if not present
            try:
                audio_file.add_tags()
            except:
                pass
            
            # Apply metadata
            if metadata.get('title'):
                audio_file.tags.add(TIT2(encoding=3, text=metadata['title']))
            if metadata.get('artist'):
                audio_file.tags.add(TPE1(encoding=3, text=metadata['artist']))
            if metadata.get('albumartist'):
                audio_file.tags.add(TPE2(encoding=3, text=metadata['albumartist']))
            if metadata.get('album'):
                audio_file.tags.add(TALB(encoding=3, text=metadata['album']))
            if metadata.get('date') or metadata.get('year'):
                year = metadata.get('date') or metadata.get('year')
                audio_file.tags.add(TDRC(encoding=3, text=str(year)))
            if metadata.get('genre'):
                audio_file.tags.add(TCON(encoding=3, text=metadata['genre']))
            
            # Add cover art if available
            if cover_art_data:
                audio_file.tags.add(
                    APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,  # Front cover
                        desc='Cover',
                        data=cover_art_data
                    )
                )
                logger.info("Added cover art to audio file")
            
            # Save the file
            audio_file.save()
            logger.info(f"Applied metadata to {audio_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying metadata to {audio_path}: {e}")
            return False
    
    async def process_job(self, job_config: Dict) -> bool:
        """Process a reconstruction job"""
        try:
            job_id = job_config.get('job_id')
            original_file = Path(job_config.get('original_file', ''))
            selected_stems = [Path(p) for p in job_config.get('selected_stems', [])]
            output_filename = job_config.get('output_filename')
            
            if not output_filename:
                output_filename = f"{original_file.stem}_reconstructed.mp3"
            
            output_path = self.output_dir / output_filename
            
            logger.info(f"Processing reconstruction job {job_id}")
            
            # Extract metadata from original file
            metadata = {}
            cover_art_data = None
            
            if original_file.exists():
                metadata = self.metadata_extractor.extract_metadata(original_file)
                cover_art_data = self.cover_extractor.extract_from_audio(original_file)
                
                # Try to find folder cover art if no embedded art
                if not cover_art_data:
                    folder_cover = self.cover_extractor.find_folder_cover_art(original_file.parent)
                    if folder_cover:
                        try:
                            with open(folder_cover, 'rb') as f:
                                cover_art_data = f.read()
                        except Exception as e:
                            logger.warning(f"Error reading folder cover art: {e}")
            
            # Process cover art if found
            if cover_art_data:
                cover_art_data = self.cover_extractor.process_cover_art(cover_art_data)
            
            # Combine stems
            if not self.combine_stems(selected_stems, output_path):
                return False
            
            # Apply metadata and cover art
            if not self.apply_metadata(output_path, metadata, cover_art_data):
                logger.warning("Failed to apply metadata, but file was created")
            
            logger.info(f"Successfully completed reconstruction job {job_id}")
            print(f"OUTPUT_FILE:{output_path}")  # For backend to capture
            return True
            
        except Exception as e:
            logger.error(f"Error processing reconstruction job: {e}")
            return False


async def process_single_job(config_file: Path):
    """Process a single reconstruction job from config file"""
    try:
        with open(config_file, 'r') as f:
            job_config = json.load(f)
        
        reconstructor = AudioReconstructor()
        success = await reconstructor.process_job(job_config)
        
        if success:
            logger.info("Single job processing completed successfully")
            return True
        else:
            logger.error("Single job processing failed")
            return False
            
    except Exception as e:
        logger.error(f"Error processing single job: {e}")
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
    logger.info("Starting Audio Reconstruction Service...")
    reconstructor = AudioReconstructor()
    
    # Example job processing
    logger.info("Audio Reconstruction Service started")
    
    # Monitor for job files
    jobs_dir = PROJECT_ROOT / "data" / "jobs" / "reconstruction"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            # Look for job files
            for job_file in jobs_dir.glob("*.json"):
                try:
                    async with aiofiles.open(job_file, 'r') as f:
                        job_config = json.loads(await f.read())
                    
                    success = await reconstructor.process_job(job_config)
                    
                    # Move job file to completed or failed
                    status_dir = jobs_dir.parent / ("completed" if success else "failed")
                    status_dir.mkdir(parents=True, exist_ok=True)
                    job_file.rename(status_dir / job_file.name)
                    
                except Exception as e:
                    logger.error(f"Error processing job file {job_file}: {e}")
            
            await asyncio.sleep(2)  # Check for new jobs every 2 seconds
            
        except KeyboardInterrupt:
            logger.info("Audio Reconstruction Service stopped")
            break
        except Exception as e:
            logger.error(f"Service error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
