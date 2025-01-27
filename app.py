from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
import os
import uuid
import subprocess
from run import run_inference

app = FastAPI()

# Temporary upload directory (ECS containers use /tmp for storage)
UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/process/")
async def process_video(
    face: str = Form(...),  # Get `face` as a string from form-data
    audio: UploadFile = File(...)
):
    """
    FastAPI endpoint to process video.

    - `face`: The filename (string) of the video in the "videos/" directory.
    - `audio`: The uploaded audio file.
    """
    
    # Construct the file path
    face_path = Path(f"videos/{face}.mp4")

    if not face_path.exists():
        raise HTTPException(status_code=400, detail=f"Face video '{face_path}' not found.")

    # Generate unique filename for the uploaded audio
    audio_path = UPLOAD_DIR / f"{uuid.uuid4()}.wav"

    # Save uploaded audio file
    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # Call run.py to process video & audio
    try:
        result_path = run_inference(video_file=face_path, vocal_file=audio_path, quality='Improved')
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
        return {"error": "Processing failed", "details": e.stderr}

# Health check endpoint
@app.get("/")
def health_check():
    return {"status": "running"}
