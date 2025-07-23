"""
Backend API endpoints for Audio Reconstruction and Music Library services
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import uuid
import aiofiles
import asyncio
from pathlib import Path
from datetime import datetime
from app.core.config import settings

router = APIRouter()

# Request/Response models
class ReconstructionRequest(BaseModel):
    job_id: Optional[str] = None
    original_file: str
    selected_stems: List[str]
    output_filename: Optional[str] = None
    preserve_metadata: bool = True
    include_cover_art: bool = True

class OrganizationRequest(BaseModel):
    job_id: Optional[str] = None
    source_files: List[str]
    target_library: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    message: Optional[str] = None
    result_file: Optional[str] = None

# Reconstruction endpoints
@router.post("/reconstruction/submit", response_model=Dict[str, str])
async def submit_reconstruction_job(request: ReconstructionRequest, background_tasks: BackgroundTasks):
    """Submit a new audio reconstruction job"""
    try:
        # Generate job ID if not provided
        job_id = request.job_id or str(uuid.uuid4())
        
        # Prepare job configuration
        job_config = {
            "job_id": job_id,
            "original_file": request.original_file,
            "selected_stems": request.selected_stems,
            "output_filename": request.output_filename,
            "preserve_metadata": request.preserve_metadata,
            "include_cover_art": request.include_cover_art,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # Save job config to a file for tracking
        jobs_dir = Path(settings.JOBS_DIR) / "reconstruction"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        job_file = jobs_dir / f"{job_id}.json"
        
        async with aiofiles.open(job_file, 'w') as f:
            await f.write(json.dumps(job_config, indent=2))
        
        # Start reconstruction as background task
        background_tasks.add_task(process_reconstruction_job, job_id, job_config)
        
        return {"job_id": job_id, "status": "submitted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit reconstruction job: {str(e)}")


async def process_reconstruction_job(job_id: str, job_config: dict):
    """Background task to process reconstruction job"""
    import subprocess
    import sys
    
    jobs_dir = Path(settings.JOBS_DIR) / "reconstruction"
    job_file = jobs_dir / f"{job_id}.json"
    
    try:
        # Update status to processing
        job_config["status"] = "processing"
        async with aiofiles.open(job_file, 'w') as f:
            await f.write(json.dumps(job_config, indent=2))
        
        # Get the project root to find virtual environments
        project_root = Path(__file__).parent.parent.parent.parent.parent
        reconstruction_venv = project_root / "audio-reconstruction-venv"
        reconstruction_python = reconstruction_venv / "bin" / "python"
        reconstruction_script = project_root / "services" / "audio-reconstruction" / "audio_reconstructor.py"
        
        # Create a temporary config file for the reconstruction service
        temp_config = {
            "original_file": job_config["original_file"],
            "selected_stems": job_config["selected_stems"],
            "output_filename": job_config.get("output_filename", f"reconstructed_{job_id}.mp3"),
            "preserve_metadata": job_config.get("preserve_metadata", True),
            "include_cover_art": job_config.get("include_cover_art", True)
        }
        
        temp_config_file = jobs_dir / f"{job_id}_config.json"
        async with aiofiles.open(temp_config_file, 'w') as f:
            await f.write(json.dumps(temp_config, indent=2))
        
        # Run the reconstruction service
        process = await asyncio.create_subprocess_exec(
            str(reconstruction_python), str(reconstruction_script), str(temp_config_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Success - extract result file path from stdout
            output_lines = stdout.decode().strip().split('\n')
            result_file = None
            for line in output_lines:
                if line.startswith("OUTPUT_FILE:"):
                    result_file = line.replace("OUTPUT_FILE:", "").strip()
                    break
            
            job_config["status"] = "completed"
            job_config["result_file"] = result_file
            job_config["completed_at"] = datetime.now().isoformat()
        else:
            # Error
            job_config["status"] = "failed"
            job_config["error"] = stderr.decode()
            job_config["completed_at"] = datetime.now().isoformat()
        
        # Clean up temp config
        if temp_config_file.exists():
            temp_config_file.unlink()
            
    except Exception as e:
        job_config["status"] = "failed"
        job_config["error"] = str(e)
        job_config["completed_at"] = datetime.now().isoformat()
    
    # Save final status
    async with aiofiles.open(job_file, 'w') as f:
        await f.write(json.dumps(job_config, indent=2))


# Organization endpoints
@router.post("/organization/submit", response_model=Dict[str, str])
async def submit_organization_job(request: OrganizationRequest, background_tasks: BackgroundTasks):
    """Submit a new music library organization job"""
    try:
        # Generate job ID if not provided
        job_id = request.job_id or str(uuid.uuid4())
        
        # Prepare job configuration
        job_config = {
            "job_id": job_id,
            "source_files": request.source_files,
            "target_library": request.target_library or settings.MUSIC_LIBRARY_DIR,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # Save job config to a file for tracking
        jobs_dir = Path(settings.JOBS_DIR) / "organization"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        job_file = jobs_dir / f"{job_id}.json"
        
        async with aiofiles.open(job_file, 'w') as f:
            await f.write(json.dumps(job_config, indent=2))
        
        # Start organization as background task
        background_tasks.add_task(process_organization_job, job_id, job_config)
        
        return {
            "job_id": job_id,
            "status": "submitted",
            "message": "Organization job submitted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit organization job: {str(e)}")


async def process_organization_job(job_id: str, job_config: dict):
    """Background task to process organization job"""
    import subprocess
    
    jobs_dir = Path(settings.JOBS_DIR) / "organization"
    job_file = jobs_dir / f"{job_id}.json"
    
    try:
        # Update status to processing
        job_config["status"] = "processing"
        async with aiofiles.open(job_file, 'w') as f:
            await f.write(json.dumps(job_config, indent=2))
        
        # Get the project root to find virtual environments
        project_root = Path(__file__).parent.parent.parent.parent.parent
        organization_venv = project_root / "music-library-venv"
        organization_python = organization_venv / "bin" / "python"
        organization_script = project_root / "services" / "music-library" / "music_organizer.py"
        
        # Create a temporary config file for the organization service
        temp_config = {
            "source_files": job_config["source_files"],
            "target_library": job_config.get("target_library", "data/music-library")
        }
        
        temp_config_file = jobs_dir / f"{job_id}_config.json"
        async with aiofiles.open(temp_config_file, 'w') as f:
            await f.write(json.dumps(temp_config, indent=2))
        
        # Run the organization service
        process = await asyncio.create_subprocess_exec(
            str(organization_python), str(organization_script), str(temp_config_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Success - extract result directory from stdout
            output_lines = stdout.decode().strip().split('\n')
            result_path = None
            for line in output_lines:
                if line.startswith("ORGANIZED_TO:"):
                    result_path = line.replace("ORGANIZED_TO:", "").strip()
                    break
            
            job_config["status"] = "completed"
            job_config["result_path"] = result_path
            job_config["completed_at"] = datetime.now().isoformat()
        else:
            # Error
            job_config["status"] = "failed"
            job_config["error"] = stderr.decode()
            job_config["completed_at"] = datetime.now().isoformat()
        
        # Clean up temp config
        if temp_config_file.exists():
            temp_config_file.unlink()
            
    except Exception as e:
        job_config["status"] = "failed"
        job_config["error"] = str(e)
        job_config["completed_at"] = datetime.now().isoformat()
    
    # Save final status
    async with aiofiles.open(job_file, 'w') as f:
        await f.write(json.dumps(job_config, indent=2))

@router.get("/reconstruction/status/{job_id}", response_model=JobStatus)
async def get_reconstruction_status(job_id: str):
    """Get status of a reconstruction job"""
    try:
        jobs_dir = Path("/tmp/reconstruction_jobs")
        job_file = jobs_dir / f"{job_id}.json"
        
        if not job_file.exists():
            raise HTTPException(status_code=404, detail="Job not found")
        
        async with aiofiles.open(job_file, 'r') as f:
            job_data = json.loads(await f.read())
        
        return JobStatus(
            job_id=job_id,
            status=job_data.get("status", "pending"),
            message=job_data.get("error", job_data.get("message")),
            result_file=job_data.get("result_file")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/organization/status/{job_id}", response_model=JobStatus)
async def get_organization_status(job_id: str):
    """Get status of an organization job"""
    try:
        jobs_dir = Path("/tmp/organization_jobs")
        job_file = jobs_dir / f"{job_id}.json"
        
        if not job_file.exists():
            raise HTTPException(status_code=404, detail="Job not found")
        
        async with aiofiles.open(job_file, 'r') as f:
            job_data = json.loads(await f.read())
        
        return JobStatus(
            job_id=job_id,
            status=job_data.get("status", "pending"),
            message=job_data.get("error", job_data.get("message")),
            result_file=job_data.get("result_path")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@router.get("/library/browse")
async def browse_music_library():
    """Browse the organized music library structure"""
    try:
        library_dir = Path(settings.MUSIC_LIBRARY_DIR)
        if not library_dir.exists():
            return {"artists": []}
        
        library_structure = {}
        
        for artist_dir in library_dir.iterdir():
            if artist_dir.is_dir():
                artist_name = artist_dir.name
                library_structure[artist_name] = {}
                
                for album_dir in artist_dir.iterdir():
                    if album_dir.is_dir():
                        album_name = album_dir.name
                        songs = []
                        
                        for song_file in album_dir.glob("*.mp3"):
                            songs.append({
                                "title": song_file.stem,
                                "path": str(song_file.relative_to(library_dir)),
                                "size": song_file.stat().st_size
                            })
                        
                        library_structure[artist_name][album_name] = songs
        
        return {"library": library_structure}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to browse library: {str(e)}")

# Utility endpoints
@router.post("/workflow/complete")
async def complete_workflow(
    original_file: str,
    selected_stems: List[str],
    background_tasks: BackgroundTasks
):
    """Complete workflow: reconstruction + organization"""
    try:
        # Submit reconstruction job
        reconstruction_request = ReconstructionRequest(
            original_file=original_file,
            selected_stems=selected_stems
        )
        
        reconstruction_result = await submit_reconstruction_job(reconstruction_request, background_tasks)
        reconstruction_job_id = reconstruction_result["job_id"]
        
        # The organization will be triggered by the reconstruction service
        # when it completes, or we can chain them here
        
        return {
            "reconstruction_job_id": reconstruction_job_id,
            "status": "workflow_started",
            "message": "Complete workflow initiated"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start complete workflow: {str(e)}")
