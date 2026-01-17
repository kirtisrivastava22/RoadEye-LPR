from fastapi import APIRouter, UploadFile, File
import cv2, re, numpy as np

from app.detector.detector import PlateDetector
from app.detector.ocr import PlateOCR
from app.database import SessionLocal
from app.models import Detection

router = APIRouter()

CONF_THRESHOLD = 0.2
PLATE_REGEX = r"^[A-Z0-9]{6,10}$"

detector = PlateDetector("yolov8n.pt")
ocr = PlateOCR()

@router.post("/image")
async def detect_image(file: UploadFile = File(...)):
    data = await file.read()
    np_img = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    detections = detector.detect(image)
    db = SessionLocal()
    results = []

    for det in detections:
        plate_text = ocr.read_plate(det["plate_crop"]).strip().upper()

        if not plate_text:
            continue
        if det["confidence"] < CONF_THRESHOLD:
            continue
        if not re.match(PLATE_REGEX, plate_text):
            continue

        record = Detection(
            plate_number=plate_text,
            confidence=det["confidence"],
            source="image"
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        results.append({
            "id": record.id,
            "plate_number": plate_text,
            "confidence": det["confidence"]
        })

    db.close()

    return {"detections": results, "count": len(results)}
