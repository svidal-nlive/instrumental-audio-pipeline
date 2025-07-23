from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import os
from typing import List, Optional
import aiofiles
import json
from ...core.config import settings
from ...models.schemas import UploadResponse, FileUploadStatus, JobCreate, SplitterType, JobType
from ...services.file_validator import FileValidator
from ...services.job_service import JobService

router = APIRouter()


@router.post("/single", response_model=UploadResponse)
async def upload_single_file(
    request: Request,
    file: UploadFile = File(...),
    splitter: str = Form(default="demucs"),
    stems_to_keep: str = Form(default='["vocals", "drums", "bass", "other"]')
):
    """Upload a single audio file for processing"""
    
    import logging
    logger = logging.getLogger("upload")
    logger.info(f"Received upload: filename={file.filename}, splitter={splitter}, stems_to_keep={stems_to_keep}")
    # Validate file
    validator = FileValidator()
    if not validator.is_valid_audio_file(file.filename):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {settings.ALLOWED_AUDIO_EXTENSIONS}"
        )
    if file.size > settings.MAX_UPLOAD_SIZE:
        logger.warning(f"File too large: {file.filename}, size={file.size}")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes"
        )
    import traceback
    try:
        # Parse stems_to_keep from JSON string
        try:
            stems_list = json.loads(stems_to_keep)
        except json.JSONDecodeError:
            stems_list = ["vocals", "drums", "bass", "other"]
        
        # Create input directory if it doesn't exist
        input_dir = Path(settings.INPUT_DIR)
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file to input directory
        file_path = input_dir / file.filename
        
        # Handle duplicate filenames
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            file_path = original_path.parent / f"{stem}_{counter}{suffix}"
            counter += 1
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create processing job
        job_service = JobService()
        job_data = JobCreate(
            filename=file_path.name,
            file_path=str(file_path),
            job_type=JobType.SINGLE,
            splitter=SplitterType(splitter.lower()),
            stems_to_keep=stems_list,
            metadata_json={"file_size": len(content)}
        )
        job = await job_service.create_job(job_data)
        
        # Start processing job in background
        await job_service.start_job(job.id)
        
        logger.info(f"Upload successful: {file_path.name}, job_id={job.id}")
        return UploadResponse(
            success=True,
            message=f"File uploaded successfully and job {job.id} created",
            file_path=str(file_path),
            filename=file_path.name,
            size=len(content)
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/batch", response_model=List[FileUploadStatus])
async def upload_batch_files(
    request: Request,
    files: List[UploadFile] = File(...)
):
    """Upload multiple audio files for batch processing"""
    
    if len(files) > 10:  # Limit batch size
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed per batch"
        )
    
    results = []
    validator = FileValidator()
    
    for file in files:
        try:
            # Validate each file
            if not validator.is_valid_audio_file(file.filename):
                results.append(FileUploadStatus(
                    filename=file.filename,
                    success=False,
                    error=f"Invalid file type: {file.filename}"
                ))
                continue
            
            if file.size > settings.MAX_UPLOAD_SIZE:
                results.append(FileUploadStatus(
                    filename=file.filename,
                    success=False,
                    error="File too large"
                ))
                continue
            
            # Create input directory if it doesn't exist
            input_dir = Path(settings.INPUT_DIR)
            input_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path = input_dir / file.filename
            
            # Handle duplicate filenames
            counter = 1
            original_path = file_path
            while file_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                file_path = original_path.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            results.append(FileUploadStatus(
                filename=file_path.name,
                success=True,
                file_path=str(file_path),
                size=len(content)
            ))
            
        except Exception as e:
            results.append(FileUploadStatus(
                filename=file.filename,
                success=False,
                error=str(e)
            ))
    
    return results


@router.post("/album")
async def upload_album(
    request: Request,
    album_name: str,
    files: List[UploadFile] = File(...)
):
    """Upload an album (multiple files in a folder)"""
    
    if not album_name or not album_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Album name is required"
        )
    
    # Sanitize album name
    album_name = "".join(c for c in album_name if c.isalnum() or c in (' ', '-', '_')).strip()
    
    try:
        # Create album directory
        album_dir = Path(settings.INPUT_DIR) / album_name
        album_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        validator = FileValidator()
        
        for file in files:
            # Validate file
            if not validator.is_valid_audio_file(file.filename):
                results.append(FileUploadStatus(
                    filename=file.filename,
                    success=False,
                    error="Invalid file type"
                ))
                continue
            
            # Save file to album directory
            file_path = album_dir / file.filename
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            results.append(FileUploadStatus(
                filename=file.filename,
                success=True,
                file_path=str(file_path),
                size=len(content)
            ))
        
        return {
            "success": True,
            "message": f"Album '{album_name}' uploaded successfully",
            "album_path": str(album_dir),
            "files": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload album: {str(e)}"
        )
