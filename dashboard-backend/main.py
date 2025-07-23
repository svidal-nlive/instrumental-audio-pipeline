from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import os

app = FastAPI(
    title="Instrumental Maker API",
    description="API for the Instrumental Maker Dashboard",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_INPUT = Path("/data/input")
MUSIC_LIBRARY = Path("/data/music-library")

# Ensure directories exist
DATA_INPUT.mkdir(parents=True, exist_ok=True)
MUSIC_LIBRARY.mkdir(parents=True, exist_ok=True)

@app.get("/")
def read_root():
    return {
        "message": "Instrumental Maker API", 
        "version": "2.0.0",
        "status": "running"
    }

@app.post("/upload/")
async def upload_files(files: list[UploadFile] = File(...)):
    uploaded = []
    for file in files:
        dest = DATA_INPUT / file.filename
        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded.append(file.filename)
    return {"uploaded": uploaded}

@app.get("/jobs/")
def get_jobs():
    # Placeholder: Replace with actual job status logic
    return {"jobs": ["Job1", "Job2"]}

@app.get("/music-library/")
def list_music_library():
    # List all files in music-library for playback
    files = []
    for root, _, filenames in os.walk(MUSIC_LIBRARY):
        for name in filenames:
            if name.endswith(".mp3"):
                files.append(os.path.relpath(os.path.join(root, name), MUSIC_LIBRARY))
    return {"files": files}

@app.get("/music-library/play/{file_path:path}")
def play_music(file_path: str):
    file = MUSIC_LIBRARY / file_path
    if file.exists():
        return FileResponse(str(file))
    return JSONResponse(status_code=404, content={"error": "File not found"})

@app.post("/settings/")
def update_settings(setting: str = Form(...), value: str = Form(...)):
    # Placeholder: Save settings to a config file or env
    return {"updated": {setting: value}}
