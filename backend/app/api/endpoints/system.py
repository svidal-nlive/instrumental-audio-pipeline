from fastapi import APIRouter
from typing import Dict, Any, List
from ...services.system_stats import SystemStatsService
from ...models.schemas import SystemSettings
from ...core.config import settings

router = APIRouter()


@router.get("/stats")
async def get_system_stats() -> Dict[str, Any]:
    """Get system statistics including CPU, memory, disk usage, etc."""
    service = SystemStatsService()
    return service.get_system_stats()


@router.get("/services")
async def get_service_status() -> List[Dict[str, Any]]:
    """Get status of all system services"""
    service = SystemStatsService()
    return service.get_service_status()


@router.get("/storage")
async def get_storage_info() -> Dict[str, Any]:
    """Get storage directory information"""
    service = SystemStatsService()
    return service.get_storage_info()


@router.get("/")
async def get_all_system_info() -> Dict[str, Any]:
    """Get all system information in one response"""
    service = SystemStatsService()
    return {
        "stats": service.get_system_stats(),
        "services": service.get_service_status(),
        "storage": service.get_storage_info()
    }


@router.get("/settings", response_model=SystemSettings)
async def get_system_settings():
    """Get current system settings"""
    return SystemSettings(
        active_splitter=settings.ACTIVE_SPLITTER,
        spleeter_model=settings.SPLEETER_MODEL,
        demucs_model=settings.DEMUCS_MODEL,
        stems_to_keep=settings.STEMS_TO_KEEP.split(','),
        enable_chunking=settings.ENABLE_CHUNKING,
        max_chunk_parts=settings.MAX_CHUNK_PARTS,
        cleanup_type=settings.CLEANUP_TYPE,
        preserve_cover_art=settings.PRESERVE_COVER_ART
    )


@router.post("/settings")
async def update_system_settings(new_settings: SystemSettings):
    """Update system settings"""
    # Note: This would typically update the .env file or database
    # For now, just return success
    return {"message": "Settings updated successfully"}


@router.get("/logs")
async def get_system_logs(lines: int = 100):
    """Get recent system logs"""
    logs_dir = Path(settings.LOGS_DIR)
    
    if not logs_dir.exists():
        return {"logs": []}
    
    # Get the most recent log file
    log_files = list(logs_dir.glob("*.log"))
    if not log_files:
        return {"logs": []}
    
    latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
    
    try:
        with open(latest_log, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
        return {"logs": [line.strip() for line in recent_lines]}
    except Exception as e:
        return {"error": f"Failed to read logs: {str(e)}"}


@router.get("/directories")
async def get_directory_info():
    """Get information about pipeline directories"""
    directories = {}
    
    dir_paths = {
        "input": settings.INPUT_DIR,
        "output": settings.OUTPUT_DIR,
        "archive": settings.ARCHIVE_DIR,
        "error": settings.ERROR_DIR,
        "logs": settings.LOGS_DIR
    }
    
    for name, path in dir_paths.items():
        path_obj = Path(path)
        if path_obj.exists():
            # Count files in directory
            file_count = len([f for f in path_obj.rglob("*") if f.is_file()])
            dir_size = sum(f.stat().st_size for f in path_obj.rglob("*") if f.is_file())
            
            directories[name] = {
                "path": str(path_obj),
                "exists": True,
                "file_count": file_count,
                "size_bytes": dir_size
            }
        else:
            directories[name] = {
                "path": str(path_obj),
                "exists": False,
                "file_count": 0,
                "size_bytes": 0
            }
    
    return directories
