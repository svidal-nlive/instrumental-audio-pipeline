from fastapi import APIRouter
from .endpoints import upload, jobs, queue, system

router = APIRouter()

# Include all endpoint routers
router.include_router(upload.router, prefix="/upload", tags=["upload"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(queue.router, prefix="/queue", tags=["queue"])
router.include_router(system.router, prefix="/system", tags=["system"])
