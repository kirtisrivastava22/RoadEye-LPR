from fastapi import APIRouter, UploadFile, File
import cv2, os, base64
import numpy as np
from datetime import datetime
from app.detector.video_pipeline import process_license_plate
from app.database import SessionLocal
from app.models import Detection

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/image")
async def detect_image(file: UploadFile = File(...)):
    data = await file.read()
    np_img = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if image is None:
        return {"detections": [], "count": 0}

    plate_crop, annotated_image, plate_text, confidence = process_license_plate(image)

    results = []
    db = SessionLocal()

    try:
        if plate_text and str(plate_text).strip():
            plate_text = plate_text.strip()

            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{plate_text}.jpg"
            abs_path = os.path.join(UPLOAD_DIR, filename)

            cv2.imwrite(abs_path, annotated_image)

            record = Detection(
                plate_number=plate_text,
                confidence=float(confidence),
                source="image",
                image_path=f"/uploads/images/{filename}"
            )

            db.add(record)
            db.commit()
            db.refresh(record)

            results.append({
                "id": record.id,
                "plate_number": record.plate_number,
                "confidence": record.confidence
            })

        _, buffer = cv2.imencode(".jpg", annotated_image)
        annotated_b64 = base64.b64encode(buffer).decode("utf-8")

        return {
            "detections": results,
            "count": len(results),
            "annotated_image": annotated_b64
        }

    finally:
        db.close()
