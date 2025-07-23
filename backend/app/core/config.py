from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Instrumental Maker API"
    
    # Project directories
    # Assuming the backend directory is inside the project root
    PROJECT_ROOT: str = str(Path(__file__).parent.parent.parent.parent.absolute())
    
    # CORS
    # Update this list to include any frontend origins (e.g., deployed React app URLs)
    # For development, '*' allows all origins (not recommended for production)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "*"
    ]
    
    # Database
    DATABASE_URL: str = "sqlite:///./instrumental_maker.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # Pipeline Settings (from existing .env)
    # Use environment variables if provided (for Docker), otherwise use project-relative paths (for local dev)
    PIPELINE_DATA_DIR: str = os.environ.get("PIPELINE_DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
    INPUT_DIR: str = os.environ.get("INPUT_DIR", os.path.join(PROJECT_ROOT, "data/input"))
    OUTPUT_DIR: str = os.environ.get("OUTPUT_DIR", os.path.join(PROJECT_ROOT, "data/output"))
    STEMS_DIR: str = os.environ.get("STEMS_DIR", os.path.join(PROJECT_ROOT, "data/stems"))
    MUSIC_LIBRARY_DIR: str = os.environ.get("MUSIC_LIBRARY_DIR", os.path.join(PROJECT_ROOT, "data/music-library"))
    ARCHIVE_DIR: str = os.environ.get("ARCHIVE_DIR", os.path.join(PROJECT_ROOT, "data/archive"))
    ERROR_DIR: str = os.environ.get("ERROR_DIR", os.path.join(PROJECT_ROOT, "data/error"))
    LOGS_DIR: str = os.environ.get("LOGS_DIR", os.path.join(PROJECT_ROOT, "data/logs"))
    TEMP_DIR: str = os.environ.get("TEMP_DIR", os.path.join(PROJECT_ROOT, "data/temp"))
    JOBS_DIR: str = os.environ.get("JOBS_DIR", os.path.join(PROJECT_ROOT, "data/jobs"))
    
    # File Watcher Settings
    FILE_STABILITY_THRESHOLD: int = 10
    DIR_STABILITY_THRESHOLD: int = 30
    
    # Queue Manager Settings
    QUEUE_FILE: str = os.environ.get("QUEUE_FILE", os.path.join(PROJECT_ROOT, "data/queue.json"))
    ENABLE_BATCH_PROCESSING: bool = True
    BATCH_SIZE: int = 1
    
    # Metadata Settings
    ENABLE_MUSICBRAINZ_LOOKUP: bool = False
    MUSICBRAINZ_RATE_LIMIT: float = 1.0
    
    # Splitter Settings
    ACTIVE_SPLITTER: str = "DEMUCS"
    STEMS_TO_KEEP: str = "drums,bass,other"
    
    # Spleeter Settings
    SPLEETER_MODEL: str = "4stems"
    
    # Demucs Settings
    DEMUCS_MODEL: str = "htdemucs"
    
    # Output Settings
    OUTPUT_SUFFIX: str = " - Instrumental ({service})"
    ENABLE_MEDIA_LIBRARY: bool = True
    CLEANUP_INTERMEDIATE_FILES: bool = True
    CLEANUP_TYPE: str = "ARCHIVE"
    CLEANUP_EMPTY_DIRS: bool = True
    PRESERVE_COVER_ART: bool = True
    
    # Chunking Settings
    ENABLE_CHUNKING: bool = True
    MAX_CHUNK_PARTS: int = 4
    CHUNK_OVERLAP_SEC: int = 5
    
    # User Settings
    PUID: int = 1001
    PGID: int = 1001
    
    # Log Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "TEXT"
    
    # Email Settings
    EMAIL_RECIPIENT: str = "recipient@example.com"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_AUDIO_EXTENSIONS: List[str] = [".mp3", ".wav", ".flac", ".m4a", ".ogg"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
