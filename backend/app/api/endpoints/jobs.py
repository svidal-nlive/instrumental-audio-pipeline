from fastapi import APIRouter, HTTPException, Depends, Request, WebSocket
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pathlib import Path
import json
import asyncio
from ...models.schemas import Job, JobStatus, JobCreate
from ...services.job_service import JobService

router = APIRouter()


@router.get("/", response_model=List[Job])
async def get_jobs(
    request: Request,
    status: Optional[JobStatus] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get list of jobs with optional filtering"""
    job_service = JobService()
    jobs = await job_service.get_jobs(status=status, limit=limit, offset=offset)
    return jobs


@router.get("/{job_id}", response_model=Job)
async def get_job(request: Request, job_id: str):
    """Get a specific job by ID"""
    job_service = JobService()
    job = await job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/", response_model=Job)
async def create_job(request: Request, job_data: JobCreate):
    """Create a new processing job"""
    job_service = JobService()
    job = await job_service.create_job(job_data)
    return job


@router.delete("/{job_id}")
async def delete_job(request: Request, job_id: str):
    """Delete a job"""
    job_service = JobService()
    success = await job_service.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully"}


@router.post("/{job_id}/retry")
async def retry_job(request: Request, job_id: str):
    """Retry a failed job"""
    job_service = JobService()
    job = await job_service.retry_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/download")
async def download_result(request: Request, job_id: str):
    """Download the processed file for a completed job"""
    job_service = JobService()
    job = await job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    def iterfile(file_path: str):
        with open(file_path, "rb") as file:
            while chunk := file.read(8192):
                yield chunk
    
    filename = Path(job.output_path).name
    return StreamingResponse(
        iterfile(job.output_path),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{job_id}/logs")
async def get_job_logs(request: Request, job_id: str):
    """Get logs for a specific job"""
    job_service = JobService()
    logs = await job_service.get_job_logs(job_id)
    return {"logs": logs}


@router.websocket("/{job_id}/progress")
async def job_progress_websocket(websocket, job_id: str):
    """WebSocket endpoint for real-time job progress"""
    await websocket.accept()
    
    job_service = JobService()
    
    try:
        # Send initial job status
        job = await job_service.get_job(job_id)
        if job:
            await websocket.send_json({
                "type": "status",
                "data": job.dict()
            })
        
        # Keep connection alive and send updates
        # This would integrate with your queue manager's event system
        while True:
            # Check for job updates
            updated_job = await job_service.get_job(job_id)
            if updated_job and updated_job != job:
                await websocket.send_json({
                    "type": "update",
                    "data": updated_job.dict()
                })
                job = updated_job
            
            # Break if job is completed or failed
            if job and job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break
                
            await asyncio.sleep(1)
            
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()
