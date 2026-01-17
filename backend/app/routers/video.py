from fastapi import APIRouter, UploadFile, File
import shutil, uuid

from app.detector.video_pipeline import process_video

router = APIRouter()

@router.post("/video")
async def detect_video(file: UploadFile = File(...)):
    temp_name = f"temp_{uuid.uuid4()}.mp4"
    with open(temp_name, "wb") as f:
        shutil.copyfileobj(file.file, f)

    success, plates = process_video(temp_name)

    return {
        "success": success,
        "plates_detected": plates
    }
