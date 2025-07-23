from pathlib import Path
from typing import List, Optional
from ..core.config import settings


class FileValidator:
    """Validates uploaded files"""
    
    def __init__(self):
        self.allowed_extensions = {ext.lower() for ext in settings.ALLOWED_AUDIO_EXTENSIONS}
        self.max_size = settings.MAX_UPLOAD_SIZE
    
    def is_valid_audio_file(self, filename: str) -> bool:
        """Check if filename has valid audio extension"""
        if not filename:
            return False
        
        path = Path(filename)
        return path.suffix.lower() in self.allowed_extensions
    
    def is_valid_size(self, size: int) -> bool:
        """Check if file size is within limits"""
        return size <= self.max_size
    
    def validate_filename(self, filename: str) -> tuple[bool, str]:
        """Validate filename and return (is_valid, error_message)"""
        if not filename:
            return False, "Filename cannot be empty"
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                return False, f"Filename contains invalid character: {char}"
        
        # Check extension
        if not self.is_valid_audio_file(filename):
            return False, f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}"
        
        return True, ""
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing/replacing invalid characters"""
        # Remove dangerous characters
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in ' .-_()[]':
                safe_chars.append(char)
            else:
                safe_chars.append('_')
        
        return ''.join(safe_chars).strip()
