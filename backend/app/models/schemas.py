from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    SINGLE = "single"
    ALBUM = "album"


class SplitterType(str, Enum):
    SPLEETER = "spleeter"
    DEMUCS = "demucs"


# Request/Response Models
class JobCreate(BaseModel):
    filename: str
    file_path: str
    job_type: JobType = JobType.SINGLE
    splitter: SplitterType = SplitterType.DEMUCS
    stems_to_keep: List[str] = ["drums", "bass", "other"]
    metadata_json: Optional[Dict[str, Any]] = None


class Job(BaseModel):
    id: str
    filename: str
    file_path: str
    output_path: Optional[str] = None
    job_type: JobType
    status: JobStatus
    splitter: SplitterType
    stems_to_keep: List[str]
    progress: int = 0
    error_message: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    success: bool
    message: str
    file_path: str
    filename: str
    size: int


class FileUploadStatus(BaseModel):
    filename: str
    success: bool
    file_path: Optional[str] = None
    size: Optional[int] = None
    error: Optional[str] = None


# Queue Models
class QueueItemStatus(str, Enum):
    DETECTED = "detected"
    STABILIZED = "stabilized"
    QUEUED = "queued"
    METADATA_FIXED = "metadata_fixed"
    SPLITTER_INPUT = "splitter_input"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class QueueItem(BaseModel):
    id: str
    path: str
    type: JobType
    block_id: Optional[str] = None
    status: QueueItemStatus
    metadata_json: Optional[Dict[str, Any]] = None
    cover_art_path: Optional[str] = None
    detected_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retries: int = 0


class QueueStatus(BaseModel):
    total_items: int
    pending_items: int
    processing_items: int
    completed_items: int
    failed_items: int
    is_paused: bool
    current_item: Optional[QueueItem] = None


# System Models
class SystemStatus(BaseModel):
    disk: Optional[Dict[str, Any]] = None
    memory: Dict[str, Any]
    cpu: Dict[str, Any]
    services: Dict[str, bool]


class SystemSettings(BaseModel):
    active_splitter: str
    spleeter_model: str
    demucs_model: str
    stems_to_keep: List[str]
    enable_chunking: bool
    max_chunk_parts: int
    cleanup_type: str
    preserve_cover_art: bool


# WebSocket Models
class WebSocketMessage(BaseModel):
    type: str
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
