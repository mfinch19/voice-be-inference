import os
import sys
import subprocess
import uuid
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
from run import run_inference
from fastapi import HTTPException


# Create FastAPI instance
app = FastAPI()

# Temporary upload directory (ECS containers use /tmp for storage)
UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/process/")
async def process_video(face: UploadFile = File(...), audio: UploadFile = File(...)):
    """
    FastAPI endpoint to process Wav2Lip.

    - Accepts uploaded `face` (video file) and `audio` (audio file).
    - Calls `run.py` to generate lip-synced output.
    - Returns the processed video file for the client to download.

    **Example Request:**
    ```bash
    curl -X 'POST' 'http://localhost:8080/process/' \
         -F 'face=@face.mp4' \
         -F 'audio=@audio.wav' \
         -o output.mp4
    ```
    """

    # Generate unique file names
    face_path = UPLOAD_DIR / f"{uuid.uuid4()}.mp4"
    audio_path = UPLOAD_DIR / f"{uuid.uuid4()}.wav"

    # Save uploaded files
    with open(face_path, "wb") as f:
        f.write(await face.read())

    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # Call run.py to process video & audio
    try:
        result_path = run_inference(video_file=face_path, vocal_file=audio_path, quality='Fast')
        print('inference result path:', result_path)
        
        if not result_path or not os.path.exists(result_path):
            raise HTTPException(status_code=500, detail="Processing failed, output file not found.")

        # Stream video file back to client
        return StreamingResponse(
            open(result_path, "rb"),
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename=processed_video.mp4"}
        )

    except subprocess.CalledProcessError as e:
        return {
            "error": "Processing failed",
            "details": e.stderr
        }

# Health check endpoint (for ECS status monitoring)
@app.get("/")
def health_check():
    return {"status": "running"}
