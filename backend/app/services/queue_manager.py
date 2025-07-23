import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..core.config import settings
from ..models.schemas import QueueItem, QueueStatus, QueueItemStatus, JobType


class QueueManager:
    """Manages the processing queue"""
    
    def __init__(self):
        self.queue_file = Path(settings.QUEUE_FILE)
        self.is_paused = False
        self._lock = asyncio.Lock()
        
        # Ensure queue file exists
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.queue_file.exists():
            self._write_queue([])
    
    async def get_queue(self) -> List[QueueItem]:
        """Get current queue items"""
        async with self._lock:
            return self._read_queue()
    
    async def get_status(self) -> QueueStatus:
        """Get queue status and statistics"""
        async with self._lock:
            items = self._read_queue()
            
            total = len(items)
            pending = len([i for i in items if i.status in [QueueItemStatus.QUEUED, QueueItemStatus.DETECTED]])
            processing = len([i for i in items if i.status == QueueItemStatus.PROCESSING])
            completed = len([i for i in items if i.status == QueueItemStatus.DONE])
            failed = len([i for i in items if i.status == QueueItemStatus.ERROR])
            
            current_item = None
            for item in items:
                if item.status == QueueItemStatus.PROCESSING:
                    current_item = item
                    break
            
            return QueueStatus(
                total_items=total,
                pending_items=pending,
                processing_items=processing,
                completed_items=completed,
                failed_items=failed,
                is_paused=self.is_paused,
                current_item=current_item
            )
    
    async def add_item(self, item: QueueItem) -> bool:
        """Add item to queue"""
        async with self._lock:
            items = self._read_queue()
            
            # Check if item already exists
            if any(i.id == item.id for i in items):
                return False
            
            items.append(item)
            self._write_queue(items)
            return True
    
    async def remove_item(self, item_id: str) -> bool:
        """Remove item from queue"""
        async with self._lock:
            items = self._read_queue()
            original_count = len(items)
            
            items = [i for i in items if i.id != item_id]
            
            if len(items) < original_count:
                self._write_queue(items)
                return True
            return False
    
    async def update_item_status(self, item_id: str, status: QueueItemStatus, **kwargs) -> bool:
        """Update item status and other fields"""
        async with self._lock:
            items = self._read_queue()
            
            for item in items:
                if item.id == item_id:
                    item.status = status
                    
                    # Update other fields if provided
                    for key, value in kwargs.items():
                        if hasattr(item, key):
                            setattr(item, key, value)
                    
                    self._write_queue(items)
                    return True
            return False
    
    async def get_next_item(self) -> Optional[QueueItem]:
        """Get next item to process"""
        if self.is_paused:
            return None
        
        async with self._lock:
            items = self._read_queue()
            
            # Find next queued item (respecting block processing)
            for item in items:
                if item.status == QueueItemStatus.QUEUED:
                    # If it's part of an album block, check if any other item from same block is processing
                    if item.block_id:
                        processing_in_block = any(
                            i.block_id == item.block_id and i.status == QueueItemStatus.PROCESSING 
                            for i in items
                        )
                        if processing_in_block:
                            continue
                    
                    return item
            return None
    
    async def set_priority(self, item_id: str, priority: int) -> bool:
        """Set item priority (lower number = higher priority)"""
        # This would require adding priority field to QueueItem model
        # For now, just return success
        return True
    
    async def pause(self):
        """Pause queue processing"""
        self.is_paused = True
    
    async def resume(self):
        """Resume queue processing"""
        self.is_paused = False
    
    async def clear(self):
        """Clear all pending items from queue"""
        async with self._lock:
            items = self._read_queue()
            # Keep only items that are currently processing or completed
            items = [i for i in items if i.status in [QueueItemStatus.PROCESSING, QueueItemStatus.DONE]]
            self._write_queue(items)
    
    def _read_queue(self) -> List[QueueItem]:
        """Read queue from file"""
        try:
            with open(self.queue_file, 'r') as f:
                data = json.load(f)
                return [QueueItem(**item) for item in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _write_queue(self, items: List[QueueItem]):
        """Write queue to file (atomic)"""
        # Convert to JSON-serializable format
        data = []
        for item in items:
            item_dict = item.dict()
            # Convert datetime objects to ISO strings
            if isinstance(item_dict.get('detected_at'), datetime):
                item_dict['detected_at'] = item_dict['detected_at'].isoformat()
            if isinstance(item_dict.get('processed_at'), datetime):
                item_dict['processed_at'] = item_dict['processed_at'].isoformat()
            data.append(item_dict)
        
        # Atomic write
        temp_file = self.queue_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        temp_file.replace(self.queue_file)
