from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.sql import func
from ..core.database import Base


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    output_path = Column(String, nullable=True)
    job_type = Column(String, nullable=False)  # single, album
    status = Column(String, nullable=False)    # pending, processing, completed, failed
    splitter = Column(String, nullable=False)  # spleeter, demucs
    stems_to_keep = Column(Text, nullable=False)  # JSON array as string
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)     # JSON as string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
