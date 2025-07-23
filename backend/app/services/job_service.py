import uuid
import json
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from ..models.schemas import Job, JobCreate, JobStatus, JobType
from ..core.config import settings
from .audio_processor import AudioProcessor


class JobService:
    """Service for managing processing jobs"""
    
    def __init__(self):
        self.jobs_file = Path(settings.LOGS_DIR) / "jobs.json"
        self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize jobs file if it doesn't exist
        if not self.jobs_file.exists():
            self._write_jobs([])
    
    async def get_jobs(self, status: Optional[JobStatus] = None, limit: int = 50, offset: int = 0) -> List[Job]:
        """Get jobs with optional filtering"""
        jobs = self._read_jobs()
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        # Sort by created_at desc
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        return jobs[offset:offset + limit]
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a specific job by ID"""
        jobs = self._read_jobs()
        return next((job for job in jobs if job.id == job_id), None)
    
    async def create_job(self, job_data: JobCreate) -> Job:
        """Create a new job"""
        job = Job(
            id=str(uuid.uuid4()),
            filename=job_data.filename,
            file_path=job_data.file_path,
            job_type=job_data.job_type,
            status=JobStatus.PENDING,
            splitter=job_data.splitter,
            stems_to_keep=job_data.stems_to_keep,
            metadata_json=job_data.metadata_json,
            created_at=datetime.now()
        )
        
        jobs = self._read_jobs()
        jobs.append(job)
        self._write_jobs(jobs)
        
        return job
    
    async def update_job(self, job_id: str, **updates) -> Optional[Job]:
        """Update a job"""
        jobs = self._read_jobs()
        
        for i, job in enumerate(jobs):
            if job.id == job_id:
                # Update fields
                for key, value in updates.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
                
                jobs[i] = job
                self._write_jobs(jobs)
                return job
        
        return None
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        jobs = self._read_jobs()
        original_count = len(jobs)
        
        jobs = [job for job in jobs if job.id != job_id]
        
        if len(jobs) < original_count:
            self._write_jobs(jobs)
            return True
        return False
    
    async def retry_job(self, job_id: str) -> Optional[Job]:
        """Retry a failed job"""
        job = await self.get_job(job_id)
        if not job or job.status != JobStatus.FAILED:
            return None
        
        # Reset job status
        updates = {
            'status': JobStatus.PENDING,
            'error_message': None,
            'progress': 0,
            'started_at': None,
            'completed_at': None
        }
        
        return await self.update_job(job_id, **updates)
    
    async def get_job_logs(self, job_id: str) -> List[str]:
        """Get logs for a specific job"""
        logs_dir = Path(settings.LOGS_DIR)
        job_log_file = logs_dir / f"job_{job_id}.log"
        
        if not job_log_file.exists():
            return []
        
        try:
            with open(job_log_file, 'r') as f:
                return f.readlines()
        except Exception:
            return []
    
    async def start_job(self, job_id: str) -> Optional[Job]:
        """Start processing a job"""
        job = await self.get_job(job_id)
        if not job or job.status != JobStatus.PENDING:
            return None
        
        # Update job to processing state
        await self.update_job(job_id, 
                            status=JobStatus.PROCESSING, 
                            started_at=datetime.now())
        
        # Start processing in background
        asyncio.create_task(self._process_job(job_id))
        
        return await self.get_job(job_id)
    
    async def _process_job(self, job_id: str):
        """Process a job in the background"""
        try:
            job = await self.get_job(job_id)
            if not job:
                return
            
            # Initialize audio processor
            processor = AudioProcessor()
            
            # Create output directory
            output_dir = Path(settings.OUTPUT_DIR) / job_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Process the audio file
            await processor.process_audio(
                input_path=job.file_path,
                output_dir=str(output_dir),
                splitter=job.splitter,
                stems_to_keep=job.stems_to_keep,
                job_id=job_id,
                progress_callback=lambda progress: asyncio.create_task(
                    self.update_job(job_id, progress=progress)
                )
            )
            
            # Update job as completed
            await self.update_job(job_id,
                                status=JobStatus.COMPLETED,
                                progress=100,
                                output_path=str(output_dir),
                                completed_at=datetime.now())
        
        except Exception as e:
            # Update job as failed
            await self.update_job(job_id,
                                status=JobStatus.FAILED,
                                error_message=str(e),
                                completed_at=datetime.now())
    
    def _read_jobs(self) -> List[Job]:
        """Read jobs from file"""
        try:
            with open(self.jobs_file, 'r') as f:
                data = json.load(f)
                jobs = []
                for item in data:
                    # Convert string dates back to datetime objects
                    if isinstance(item.get('created_at'), str):
                        item['created_at'] = datetime.fromisoformat(item['created_at'])
                    if isinstance(item.get('started_at'), str):
                        item['started_at'] = datetime.fromisoformat(item['started_at'])
                    if isinstance(item.get('completed_at'), str):
                        item['completed_at'] = datetime.fromisoformat(item['completed_at'])
                    
                    jobs.append(Job(**item))
                return jobs
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _write_jobs(self, jobs: List[Job]):
        """Write jobs to file"""
        data = []
        for job in jobs:
            job_dict = job.dict()
            # Convert datetime objects to ISO strings
            if isinstance(job_dict.get('created_at'), datetime):
                job_dict['created_at'] = job_dict['created_at'].isoformat()
            if isinstance(job_dict.get('started_at'), datetime):
                job_dict['started_at'] = job_dict['started_at'].isoformat()
            if isinstance(job_dict.get('completed_at'), datetime):
                job_dict['completed_at'] = job_dict['completed_at'].isoformat()
            data.append(job_dict)
        
        # Atomic write
        temp_file = self.jobs_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        temp_file.replace(self.jobs_file)
