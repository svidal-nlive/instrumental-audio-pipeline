import asyncio
import subprocess
import shutil
import json
from pathlib import Path
from typing import List, Callable, Optional
from ..core.config import settings


class AudioProcessor:
    """Service for processing audio files with various splitters"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent  # Go up to project root
        self.spleeter_venv = self.project_root / "spleeter-venv"
        self.demucs_venv = self.project_root / "demucs-venv"
        self.demucs_available = self._check_demucs()
        self.spleeter_available = self._check_spleeter()
    
    def _check_demucs(self) -> bool:
        """Check if Demucs virtual environment is available"""
        demucs_python = self.demucs_venv / "bin" / "python"
        try:
            result = subprocess.run([str(demucs_python), "-c", "import audio_separator"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_spleeter(self) -> bool:
        """Check if Spleeter virtual environment is available"""
        spleeter_python = self.spleeter_venv / "bin" / "python"
        try:
            result = subprocess.run([str(spleeter_python), "-c", "import spleeter"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    async def process_audio(
        self,
        input_path: str,
        output_dir: str,
        splitter: str,
        stems_to_keep: List[str],
        job_id: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ):
        """Process audio file and extract stems"""
        
        input_file = Path(input_path)
        output_path = Path(output_dir)
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Update progress
        if progress_callback:
            progress_callback(10)
        
        if splitter.lower() == "demucs":
            await self._process_with_demucs(input_file, output_path, stems_to_keep, progress_callback)
        elif splitter.lower() == "spleeter":
            await self._process_with_spleeter(input_file, output_path, stems_to_keep, progress_callback)
        else:
            raise ValueError(f"Unknown splitter: {splitter}")
        
        # Final progress update
        if progress_callback:
            progress_callback(100)
    
    async def _process_with_demucs(
        self,
        input_file: Path,
        output_dir: Path,
        stems_to_keep: List[str],
        progress_callback: Optional[Callable[[int], None]] = None
    ):
        """Process audio with Demucs using subprocess"""
        if progress_callback:
            progress_callback(20)
            
        # Create stems directory
        stems_dir = output_dir / 'stems'
        stems_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a Python script to run audio-separator (demucs)
        script_content = f'''
import sys
from pathlib import Path
from audio_separator.separator import Separator

# Set up paths
input_file = Path("{input_file}")
output_dir = Path("{stems_dir}")

print(f"Processing {{input_file}} with audio-separator")

# Create separator instance
separator = Separator()

# Process the file
output_files = separator.separate(str(input_file), output_dir=str(output_dir))

print(f"Separation completed. Output files: {{output_files}}")
'''
        
        # Write the script to a temporary file
        script_file = output_dir / "demucs_script.py"
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        if progress_callback:
            progress_callback(40)
        
        # Run the script with the demucs virtual environment
        demucs_python = self.demucs_venv / "bin" / "python"
        cmd = [str(demucs_python), str(script_file)]
        
        try:
            if progress_callback:
                progress_callback(60)
                
            # Run the demucs process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(output_dir)
            )
            stdout, stderr = await process.communicate()
            
            if progress_callback:
                progress_callback(80)
            
            if process.returncode != 0:
                raise RuntimeError(f"Demucs/audio-separator failed: {stderr.decode()}")
                
            # Clean up script file
            script_file.unlink()
            
            # Create a summary file
            summary_file = output_dir / "processing_summary.txt"
            with open(summary_file, 'w') as f:
                f.write(f"Processed: {input_file.name}\\n")
                f.write(f"Stems created: {', '.join(stems_to_keep)}\\n")
                f.write(f"Output directory: {output_dir}\\n")
                f.write(f"Demucs stdout: {stdout.decode()}\\n")
                
        except Exception as e:
            # Clean up script file on error
            if script_file.exists():
                script_file.unlink()
            raise e
    
    async def _process_with_spleeter(
        self,
        input_file: Path,
        output_dir: Path,
        stems_to_keep: List[str],
        progress_callback: Optional[Callable[[int], None]] = None
    ):
        """Process audio with Spleeter using subprocess"""
        if progress_callback:
            progress_callback(20)
            
        # Create a temporary script to run spleeter in the correct virtual environment
        stems_dir = output_dir / 'stems'
        stems_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a Python script to run spleeter
        script_content = f'''
import sys
from pathlib import Path
from spleeter.separator import Separator
import tensorflow as tf

# Disable TensorFlow warnings
tf.get_logger().setLevel('ERROR')

# Set up paths
input_file = Path("{input_file}")
output_dir = Path("{stems_dir}")

# Determine model based on stems requested
stems_to_keep = {stems_to_keep}
if "vocals" in stems_to_keep and "accompaniment" in stems_to_keep:
    model = "spleeter:2stems-16kHz"
elif len(stems_to_keep) == 4:
    model = "spleeter:4stems-16kHz"
elif len(stems_to_keep) == 5:
    model = "spleeter:5stems-16kHz"
else:
    model = "spleeter:2stems-16kHz"  # Default

print(f"Using model: {{model}}")

# Create separator and process
separator = Separator(model)
print(f"Separating {{input_file}} to {{output_dir}}")
separator.separate_to_file(str(input_file), str(output_dir))

print("Spleeter processing completed successfully")
'''
        
        # Write the script to a temporary file
        script_file = output_dir / "spleeter_script.py"
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        if progress_callback:
            progress_callback(40)
        
        # Run the script with the spleeter virtual environment
        spleeter_python = self.spleeter_venv / "bin" / "python"
        cmd = [str(spleeter_python), str(script_file)]
        
        try:
            if progress_callback:
                progress_callback(60)
                
            # Run the spleeter process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(output_dir)
            )
            stdout, stderr = await process.communicate()
            
            if progress_callback:
                progress_callback(80)
            
            if process.returncode != 0:
                raise RuntimeError(f"Spleeter failed: {stderr.decode()}")
                
            # Clean up script file
            script_file.unlink()
            
            # Create a summary file
            summary_file = output_dir / "processing_summary.txt"
            with open(summary_file, 'w') as f:
                f.write(f"Processed: {input_file.name}\\n")
                f.write(f"Stems created: {', '.join(stems_to_keep)}\\n")
                f.write(f"Output directory: {output_dir}\\n")
                f.write(f"Spleeter stdout: {stdout.decode()}\\n")
                
        except Exception as e:
            # Clean up script file on error
            if script_file.exists():
                script_file.unlink()
            raise e
    
    async def _create_dummy_stems(
        self,
        input_file: Path,
        output_dir: Path,
        stems_to_keep: List[str],
        progress_callback: Optional[Callable[[int], None]] = None
    ):
        """Create dummy stem files for demonstration"""
        
        # Create stems directory
        stems_dir = output_dir / "stems"
        stems_dir.mkdir(parents=True, exist_ok=True)
        
        total_stems = len(stems_to_keep)
        
        for i, stem in enumerate(stems_to_keep):
            # Simulate processing time
            await asyncio.sleep(1)
            
            # Create dummy file (copy original file as placeholder)
            stem_file = stems_dir / f"{input_file.stem}_{stem}.wav"
            
            # Copy original file as a placeholder
            # In real implementation, this would be the actual separated stem
            shutil.copy2(input_file, stem_file)
            
            # Update progress
            if progress_callback:
                progress = 30 + (60 * (i + 1) // total_stems)
                progress_callback(progress)
        
        # Create a summary file
        summary_file = output_dir / "processing_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Processed: {input_file.name}\n")
            f.write(f"Stems created: {', '.join(stems_to_keep)}\n")
            f.write(f"Output directory: {output_dir}\n")
    
    def get_available_splitters(self) -> List[str]:
        """Get list of available splitters"""
        splitters = []
        if self.demucs_available:
            splitters.append("demucs")
        if self.spleeter_available:
            splitters.append("spleeter")
        
        # Always include at least one for demo purposes
        if not splitters:
            splitters = ["demucs", "spleeter"]
        
        return splitters
