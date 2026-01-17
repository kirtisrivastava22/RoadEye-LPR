from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile
import cv2
import numpy as np
from app.detector import PlateDetector
from app.ocr import PlateOCR
from app.database import engine, SessionLocal
from app.models import Detection
import re


app = FastAPI(title="RoadEye-LPR API")
ocr = PlateOCR()
CONF_THRESHOLD = 0.6
PLATE_REGEX = r"^[A-Z0-9]{6,10}$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "API running"}


detector = PlateDetector("C:/Users/kirti/OneDrive/Desktop/New folder/RoadEye-LPR/yolov8n.pt")
Detection.__table__.create(bind=engine, checkfirst=True)

@app.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):
    data = await file.read()
    np_img = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    detections = detector.detect(image)
    db = SessionLocal()

    results = []
    for det in detections:
        plate_text = ocr.read_plate(det["plate_crop"])
        plate_text = plate_text.strip().upper()

        #Skip empty OCR
        if not plate_text:
            continue

        # Skip low confidence detections
        if det["confidence"] < CONF_THRESHOLD:
            continue

        #Skip invalid plate formats
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

    return {
        "detections": results,
        "count": len(results)
    }
    
@app.get("/history")
def get_history():
    db = SessionLocal()
    records = db.query(Detection).order_by(Detection.timestamp.desc()).all()
    db.close()

    return [
        {
            "id": r.id,
            "plate_number": r.plate_number,
            "confidence": r.confidence,
            "timestamp": r.timestamp
        }
        for r in records
    ]
