import asyncio
import time
from pathlib import Path
from typing import Dict, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ..core.config import settings
from ..models.schemas import QueueItem, QueueItemStatus, JobType
from .queue_manager import QueueManager
import uuid
from datetime import datetime


class StabilityTracker:
    """Tracks file/directory stability"""
    
    def __init__(self, file_threshold: int, dir_threshold: int):
        self.file_threshold = file_threshold
        self.dir_threshold = dir_threshold
        self.tracked_items: Dict[str, float] = {}  # path -> last_modified_time
        self.stable_callbacks = []
    
    def update_item(self, path: str):
        """Update last modified time for an item"""
        self.tracked_items[path] = time.time()
    
    def remove_item(self, path: str):
        """Remove item from tracking"""
        self.tracked_items.pop(path, None)
    
    def get_stable_items(self) -> Set[str]:
        """Get items that are stable"""
        current_time = time.time()
        stable_items = set()
        
        for path, last_modified in self.tracked_items.items():
            path_obj = Path(path)
            threshold = self.dir_threshold if path_obj.is_dir() else self.file_threshold
            
            if current_time - last_modified >= threshold:
                stable_items.add(path)
        
        return stable_items
    
    def add_stable_callback(self, callback):
        """Add callback for when items become stable"""
        self.stable_callbacks.append(callback)


class PipelineFileHandler(FileSystemEventHandler):
    """Handles file system events for the pipeline"""
    
    def __init__(self, stability_tracker: StabilityTracker):
        self.stability_tracker = stability_tracker
        self.allowed_extensions = {ext.lower() for ext in settings.ALLOWED_AUDIO_EXTENSIONS}
    
    def on_created(self, event):
        if not event.is_directory:
            path = Path(event.src_path)
            if self._is_audio_file(path):
                self.stability_tracker.update_item(event.src_path)
        else:
            self.stability_tracker.update_item(event.src_path)
    
    def on_modified(self, event):
        self.stability_tracker.update_item(event.src_path)
    
    def on_moved(self, event):
        # Remove old path and add new path
        self.stability_tracker.remove_item(event.src_path)
        if not event.is_directory:
            path = Path(event.dest_path)
            if self._is_audio_file(path):
                self.stability_tracker.update_item(event.dest_path)
        else:
            self.stability_tracker.update_item(event.dest_path)
    
    def on_deleted(self, event):
        self.stability_tracker.remove_item(event.src_path)
    
    def _is_audio_file(self, path: Path) -> bool:
        """Check if file is an audio file"""
        return path.suffix.lower() in self.allowed_extensions


class FileWatcher:
    """Watches for file changes and manages the processing queue"""
    
    def __init__(self, queue_manager: QueueManager):
        self.queue_manager = queue_manager
        self.observer = Observer()
        self.stability_tracker = StabilityTracker(
            settings.FILE_STABILITY_THRESHOLD,
            settings.DIR_STABILITY_THRESHOLD
        )
        self.handler = PipelineFileHandler(self.stability_tracker)
        self._running = False
        self._check_task = None
    
    async def start(self):
        """Start the file watcher"""
        if self._running:
            return
        
        # Create input directory if it doesn't exist
        input_dir = Path(settings.INPUT_DIR)
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up file system watcher
        self.observer.schedule(self.handler, str(input_dir), recursive=True)
        self.observer.start()
        
        # Start periodic stability check
        self._running = True
        self._check_task = asyncio.create_task(self._periodic_stability_check())
    
    async def stop(self):
        """Stop the file watcher"""
        self._running = False
        
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
    
    async def _periodic_stability_check(self):
        """Periodically check for stable items and add them to queue"""
        while self._running:
            try:
                stable_items = self.stability_tracker.get_stable_items()
                
                for item_path in stable_items:
                    await self._process_stable_item(item_path)
                    self.stability_tracker.remove_item(item_path)
                
                await asyncio.sleep(5)  # Check every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue
                print(f"Error in stability check: {e}")
                await asyncio.sleep(5)
    
    async def _process_stable_item(self, item_path: str):
        """Process a stable item and add to queue"""
        path = Path(item_path)
        
        if not path.exists():
            return
        
        try:
            if path.is_file():
                # Single file
                if self._is_audio_file(path):
                    await self._add_single_file_to_queue(path)
            else:
                # Directory (album)
                await self._add_album_to_queue(path)
        except Exception as e:
            print(f"Error processing stable item {item_path}: {e}")
    
    async def _add_single_file_to_queue(self, file_path: Path):
        """Add a single file to the queue"""
        queue_item = QueueItem(
            id=str(uuid.uuid4()),
            path=str(file_path),
            type=JobType.SINGLE,
            status=QueueItemStatus.QUEUED,
            detected_at=datetime.now()
        )
        
        await self.queue_manager.add_item(queue_item)
    
    async def _add_album_to_queue(self, dir_path: Path):
        """Add an album (directory) to the queue"""
        # Find all audio files in the directory
        audio_files = []
        for file in dir_path.rglob("*"):
            if file.is_file() and self._is_audio_file(file):
                audio_files.append(file)
        
        if not audio_files:
            return
        
        # Generate block ID for the album
        block_id = str(uuid.uuid4())
        
        # Add each file as a queue item with the same block_id
        for audio_file in sorted(audio_files):  # Sort to maintain order
            queue_item = QueueItem(
                id=str(uuid.uuid4()),
                path=str(audio_file),
                type=JobType.ALBUM,
                block_id=block_id,
                status=QueueItemStatus.QUEUED,
                detected_at=datetime.now()
            )
            
            await self.queue_manager.add_item(queue_item)
    
    def _is_audio_file(self, path: Path) -> bool:
        """Check if file is an audio file"""
        return path.suffix.lower() in {ext.lower() for ext in settings.ALLOWED_AUDIO_EXTENSIONS}
