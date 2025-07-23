import psutil
import shutil
import os
import subprocess
import time
import yaml
from pathlib import Path
from typing import Dict, Any, List, Set
from datetime import datetime, timedelta
from ..core.config import settings


class SystemStatsService:
    """Service for collecting system statistics and information"""
    
    def __init__(self):
        self.start_time = time.time()
        self.project_name = "instrumental-maker"  # Default project name
        self.expected_services = self._get_expected_services()
        
    def _get_expected_services(self) -> Set[str]:
        """Parse docker-compose files to get expected service names"""
        try:
            expected_services = set()
            
            # List of docker-compose files to check
            compose_files = [
                os.path.join(settings.PROJECT_ROOT, "docker-compose.yml"),
                os.path.join(settings.PROJECT_ROOT, "docker-compose.prod.yml")
            ]
            
            for compose_file in compose_files:
                if not os.path.exists(compose_file):
                    print(f"Warning: docker-compose file not found at {compose_file}")
                    continue
                    
                with open(compose_file, 'r') as f:
                    compose_data = yaml.safe_load(f)
                    
                services = compose_data.get('services', {})
                # Extract service names and convert them to container names
                for service_name in services.keys():
                    # Check if container_name is explicitly defined
                    container_name = services[service_name].get('container_name')
                    if container_name:
                        expected_services.add(container_name)
                    else:
                        # Docker Compose auto-generates container names as project_service
                        expected_services.add(f"{self.project_name}-{service_name}")
            
            # Also add Demucs if it exists in the services directory
            if os.path.exists(os.path.join(settings.PROJECT_ROOT, "services/demucs")):
                expected_services.add(f"{self.project_name}-demucs")
                expected_services.add(f"{self.project_name}-demucs-prod")
                
            print(f"Expected services from docker-compose files: {expected_services}")
            return expected_services
        except Exception as e:
            print(f"Error parsing docker-compose files: {str(e)}")
            return set()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics including CPU, memory, disk, and service status"""
        uptime_seconds = int(time.time() - self.start_time)
        uptime = self._format_uptime(uptime_seconds)
        
        # Get Docker container info
        container_info = self._get_docker_container_info()
        running_service_names = {container['name'] for container in container_info}
        
        # Create a complete services list with running and non-running services
        all_services = []
        
        # Add running containers first
        for container in container_info:
            all_services.append({
                'id': container['id'],
                'name': container['name'],
                'image': container['image'],
                'status': container['status'],
                'created': container['created'],
                'running': container['status'].lower().startswith('up')
            })
        
        # Add expected but not running services
        for service_name in self.expected_services:
            if service_name not in running_service_names:
                all_services.append({
                    'id': 'N/A',
                    'name': service_name,
                    'image': 'N/A',
                    'status': 'not created',
                    'created': 'N/A',
                    'running': False
                })
        
        return {
            "cpu": {
                "usage": psutil.cpu_percent(interval=0.1),
                "cores": psutil.cpu_count(logical=True)
            },
            "memory": {
                "total": self._format_bytes(psutil.virtual_memory().total),
                "used": self._format_bytes(psutil.virtual_memory().used),
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": self._format_bytes(shutil.disk_usage("/").total),
                "used": self._format_bytes(shutil.disk_usage("/").used),
                "percent": shutil.disk_usage("/").used / shutil.disk_usage("/").total * 100
            },
            "system": {
                "uptime": uptime
            },
            "services": all_services
        }
    
    def get_service_status(self) -> List[Dict[str, Any]]:
        """Get the status of all services"""
        # Get Docker container info
        container_info = self._get_docker_container_info()
        running_service_names = {container['name'] for container in container_info}
        
        # Create a complete services list with running and non-running services
        all_services = []
        
        # Add running containers first
        for container in container_info:
            is_running = container['status'].lower().startswith('up')
            
            # Extract service name from container name
            service_name = container['name']
            # If container name has a prefix (like instrumental-maker-backend), extract the service part
            if '-' in service_name:
                service_parts = service_name.split('-')
                if len(service_parts) >= 3:  # project-name-service
                    service_name = ' '.join(part.capitalize() for part in service_parts[2:])
            
            # Map container name to a friendly service name
            service_friendly_names = {
                "instrumental-maker-backend": "Backend API",
                "instrumental-maker-frontend": "Frontend Web App",
                "instrumental-maker-redis": "Redis",
                "instrumental-maker-postgres": "PostgreSQL Database",
                "instrumental-maker-nginx": "Nginx",
                "instrumental-maker-spleeter": "Spleeter Service",
                "instrumental-maker-demucs": "Demucs Service",
                "instrumental-maker-backend-prod": "Backend API (Prod)",
                "instrumental-maker-frontend-prod": "Frontend Web App (Prod)",
                "instrumental-maker-redis-prod": "Redis (Prod)",
                "instrumental-maker-postgres-prod": "PostgreSQL Database (Prod)",
                "instrumental-maker-nginx-prod": "Nginx (Prod)",
                "instrumental-maker-spleeter-prod": "Spleeter Service (Prod)",
                "instrumental-maker-demucs-prod": "Demucs Service (Prod)"
            }
            
            friendly_name = service_friendly_names.get(container['name'], service_name)
            
            all_services.append({
                "name": friendly_name,
                "status": "running" if is_running else container['status'],
                "container_id": container['id'],
                "image": container['image'],
                "created": container['created'],
                "state": container['status'],
                "health": "healthy" if is_running else "unhealthy",
                "uptime": self._get_uptime() if is_running else "",
                "version": self._extract_version_from_image(container['image'])
            })
        
        # Add expected but not running services
        for service_name in self.expected_services:
            if service_name not in running_service_names:
                # Map to friendly name if it exists
                service_friendly_names = {
                    "instrumental-maker-backend": "Backend API",
                    "instrumental-maker-frontend": "Frontend Web App",
                    "instrumental-maker-redis": "Redis",
                    "instrumental-maker-postgres": "PostgreSQL Database",
                    "instrumental-maker-nginx": "Nginx",
                    "instrumental-maker-spleeter": "Spleeter Service",
                    "instrumental-maker-demucs": "Demucs Service",
                    "instrumental-maker-backend-prod": "Backend API (Prod)",
                    "instrumental-maker-frontend-prod": "Frontend Web App (Prod)",
                    "instrumental-maker-redis-prod": "Redis (Prod)",
                    "instrumental-maker-postgres-prod": "PostgreSQL Database (Prod)",
                    "instrumental-maker-nginx-prod": "Nginx (Prod)",
                    "instrumental-maker-spleeter-prod": "Spleeter Service (Prod)",
                    "instrumental-maker-demucs-prod": "Demucs Service (Prod)"
                }
                
                friendly_name = service_friendly_names.get(service_name, service_name)
                
                all_services.append({
                    "name": friendly_name,
                    "status": "stopped",
                    "container_id": "N/A",
                    "image": "N/A",
                    "created": "N/A",
                    "state": "stopped",
                    "health": "unhealthy",
                    "uptime": "",
                    "version": ""
                })
                
        return all_services
        
    def _extract_version_from_image(self, image_name: str) -> str:
        """Extract version from image tag if available"""
        try:
            if ':' in image_name:
                tag = image_name.split(':')[1]
                # If tag is something like "3.9-alpine", extract the 3.9 part
                if '-' in tag:
                    version = tag.split('-')[0]
                    return version
                return tag
        except Exception:
            pass
        return "latest"
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage directory information"""
        return {
            "input_directory": {
                "path": str(settings.INPUT_DIR),
                "size": self._get_directory_size(settings.INPUT_DIR),
                "files_count": self._count_files(settings.INPUT_DIR)
            },
            "output_directory": {
                "path": str(settings.OUTPUT_DIR),
                "size": self._get_directory_size(settings.OUTPUT_DIR),
                "files_count": self._count_files(settings.OUTPUT_DIR)
            },
            "archive_directory": {
                "path": str(settings.ARCHIVE_DIR),
                "size": self._get_directory_size(settings.ARCHIVE_DIR),
                "files_count": self._count_files(settings.ARCHIVE_DIR)
            },
            "logs_directory": {
                "path": str(settings.LOGS_DIR),
                "size": self._get_directory_size(settings.LOGS_DIR),
                "files_count": self._count_files(settings.LOGS_DIR)
            }
        }
    
    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        return round(psutil.cpu_percent(interval=1), 1)
    
    def _get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        memory = psutil.virtual_memory()
        return round(memory.percent, 1)
    
    def _get_disk_usage(self) -> float:
        """Get disk usage percentage for the current directory"""
        try:
            total, used, free = shutil.disk_usage("/")
            return round((used / total) * 100, 1)
        except Exception:
            return 0.0
    
    def _is_gpu_available(self) -> bool:
        """Check if GPU is available"""
        try:
            # Try to run nvidia-smi to check for NVIDIA GPU
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _get_gpu_usage(self) -> float:
        """Get GPU usage percentage"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError, ValueError):
            pass
        return 0.0
    
    def _format_bytes(self, size: int) -> str:
        """Format bytes to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
        
    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in seconds to a human-readable string"""
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} days, {hours} hours, {minutes} minutes"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes, {seconds} seconds"
    
    def _get_uptime(self) -> str:
        """Get system uptime"""
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_delta = timedelta(seconds=int(uptime_seconds))
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            return f"{days} days, {hours} hours"
        except Exception:
            return "Unknown"
    
    def _check_redis_status(self) -> str:
        """Check if Redis is running by looking for its container"""
        containers = self._get_docker_container_info()
        for container in containers:
            if "redis" in container["name"].lower():
                if container["status"].lower().startswith("up"):
                    return "running"
                else:
                    return container["status"]
        
        # Fallback to checking Redis connection
        try:
            import redis
            # Try to extract host and port from REDIS_URL if it's a valid URI
            host = getattr(settings, 'REDIS_HOST', 'localhost')
            port = getattr(settings, 'REDIS_PORT', 6379)
            
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL and '://' in settings.REDIS_URL:
                # Parse from REDIS_URL (redis://hostname:port)
                from urllib.parse import urlparse
                parsed_url = urlparse(settings.REDIS_URL)
                if parsed_url.hostname:
                    host = parsed_url.hostname
                if parsed_url.port:
                    port = parsed_url.port
            
            # Connect and check status
            r = redis.Redis(host=host, port=port, db=0, socket_connect_timeout=2)
            r.ping()
            return "running"
        except Exception as e:
            print(f"Redis connection error: {str(e)}")
            return "stopped"
    
    def _check_demucs_availability(self) -> str:
        """Check if Demucs is available by looking for its container"""
        containers = self._get_docker_container_info()
        for container in containers:
            if "demucs" in container["name"].lower():
                if container["status"].lower().startswith("up"):
                    return "running"
                else:
                    return container["status"]
        
        # Fallback to checking for Python module
        try:
            result = subprocess.run(['python', '-c', 'import demucs'], 
                                  capture_output=True, text=True, timeout=5)
            return "running" if result.returncode == 0 else "stopped"
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return "stopped"
    
    def _check_spleeter_availability(self) -> str:
        """Check if Spleeter is available by looking for its container"""
        containers = self._get_docker_container_info()
        for container in containers:
            if "spleeter" in container["name"].lower():
                if container["status"].lower().startswith("up"):
                    return "running"
                else:
                    return container["status"]
        
        # Fallback to checking for Python module
        try:
            result = subprocess.run(['python', '-c', 'import spleeter'], 
                                  capture_output=True, text=True, timeout=5)
            return "running" if result.returncode == 0 else "stopped"
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return "stopped"
    

    def _get_docker_container_info(self) -> List[Dict[str, Any]]:
        """Get Docker container information using the Docker socket, filtering by expected services from docker-compose.yml"""
        try:
            # Try to use the Docker Python SDK
            import docker
            try:
                client = docker.from_env()
                containers = client.containers.list(all=True)
                
                # Filter containers to only include those in our expected services list
                project_containers = []
                for container in containers:
                    # Check if container is in our expected services
                    is_expected = False
                    
                    # First check exact match with expected services from docker-compose
                    if self.expected_services and container.name in self.expected_services:
                        is_expected = True
                    # Fallback to project name prefix if we couldn't parse the compose file
                    elif not self.expected_services and container.name.startswith(f"{self.project_name}-"):
                        is_expected = True
                    
                    if is_expected:
                        # Parse container information
                        image_name = container.image.tags[0] if container.image.tags else str(container.image.id)
                        created_date = container.attrs.get('Created', '')
                        try:
                            created_datetime = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                            # Format date as: Jan 01, 2023
                            created_str = created_datetime.strftime('%b %d, %Y')
                        except:
                            created_str = "Unknown"
                            
                        project_containers.append({
                            'id': container.id[:12],
                            'name': container.name,
                            'image': image_name,
                            'status': container.status,
                            'created': created_str
                        })
                
                print(f"Found {len(project_containers)} Docker containers matching our services")
                return project_containers
            except Exception as e:
                print(f"Error using Docker Python SDK: {str(e)}")
                raise
                
        except ImportError:
            # Fallback to using the docker command line if SDK is not available
            try:
                result = subprocess.run(
                    ['docker', 'ps', '-a', '--format', '{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.CreatedAt}}'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:  # Skip empty lines
                        parts = line.split('\t')
                        if len(parts) >= 5:
                            container_id, name, image, status, created = parts[:5]
                            
                            # Check if container is in our expected services
                            is_expected = False
                            
                            # First check exact match with expected services from docker-compose
                            if self.expected_services and name in self.expected_services:
                                is_expected = True
                            # Fallback to project name prefix if we couldn't parse the compose file
                            elif not self.expected_services and name.startswith(f"{self.project_name}-"):
                                is_expected = True
                            
                            if is_expected:
                                try:
                                    # Parse created date to reformat it
                                    # Example format: 2023-01-01 00:00:00 +0000 UTC
                                    created_parts = created.split(' ')
                                    if len(created_parts) >= 2:
                                        date_str = created_parts[0]
                                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                        created = date_obj.strftime('%b %d, %Y')
                                except:
                                    pass  # Keep original format if parsing fails
                                
                                containers.append({
                                    'id': container_id[:12],
                                    'name': name,
                                    'image': image,
                                    'status': status,
                                    'created': created
                                })
                
                print(f"Found {len(containers)} Docker containers matching our services using command line")
                return containers
            except Exception as e:
                print(f"Error getting Docker container info using command line: {str(e)}")
                return []
                
        return []
    def _calculate_container_uptime(self, started_at: str) -> str:
        """Calculate container uptime from start time"""
        try:
            import datetime
            from dateutil import parser
            
            # Parse the timestamp
            start_time = parser.parse(started_at)
            now = datetime.datetime.now(start_time.tzinfo)
            
            # Calculate the difference
            delta = now - start_time
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            
            return f"{days} days, {hours} hours"
        except Exception:
            return "Unknown"
            
    def _extract_version_from_image(self, image: str) -> str:
        """Extract version from Docker image name"""
        # Example: redis:7-alpine -> 7-alpine
        if ':' in image:
            return image.split(':')[-1]
        return "latest"
    
    def _get_jobs_processed_today(self) -> int:
        """Get number of jobs processed today"""
        try:
            import sys
            sys.path.append('/app')
            from app.services.job_service import JobService
            job_service = JobService()
            jobs = job_service._read_jobs()
            
            today = datetime.now().date()
            count = 0
            for job in jobs:
                if hasattr(job, 'completed_at') and job.completed_at and job.completed_at.date() == today:
                    count += 1
            return count
        except Exception as e:
            print(f"Error getting jobs processed today: {e}")
            return 0
    
    def _get_total_files_processed(self) -> int:
        """Get total number of files processed"""
        try:
            import sys
            sys.path.append('/app')
            from app.services.job_service import JobService
            job_service = JobService()
            jobs = job_service._read_jobs()
            
            count = 0
            for job in jobs:
                if hasattr(job, 'status') and job.status.value == "completed":
                    count += 1
            return count
        except Exception as e:
            print(f"Error getting total files processed: {e}")
            return 0
    
    def _get_directory_size(self, directory: str) -> int:
        """Get total size of directory in bytes"""
        try:
            path = Path(directory)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                return 0
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        pass
            return total_size
        except Exception:
            return 0
    
    def _count_files(self, directory: str) -> int:
        """Count number of files in directory"""
        try:
            path = Path(directory)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                return 0
            
            count = 0
            for dirpath, dirnames, filenames in os.walk(path):
                count += len(filenames)
            return count
        except Exception:
            return 0
