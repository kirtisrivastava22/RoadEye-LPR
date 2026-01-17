# app/routers/image.py
from fastapi import APIRouter, UploadFile, File
import cv2
import numpy as np
import base64
from datetime import datetime
from app.detector.video_pipeline import process_license_plate
from app.database import SessionLocal
from app.models import Detection
import os

router = APIRouter()

# Create directory for storing images
UPLOAD_DIR = "uploads/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/image")
async def detect_image(file: UploadFile = File(...)):
    """Detect license plates in uploaded image"""
    
    # Read and decode image
    data = await file.read()
    np_img = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    
    if image is None:
        return {"error": "Invalid image", "detections": []}
    
    # Process image with your detection pipeline
    plate_crop, annotated_image, plate_text, confidence = process_license_plate(image)
    
    results = []
    db = SessionLocal()
    
    try:
        if plate_text and confidence > 0.15:  # Confidence threshold
            # Save annotated image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{timestamp}_{plate_text}.jpg"
            image_path = os.path.join(UPLOAD_DIR, image_filename)
            cv2.imwrite(image_path, annotated_image)
            
            # Save to database
            record = Detection(
                plate_number=plate_text,
                confidence=float(confidence),
                source="image",
                image_path=f"/uploads/images/{image_filename}"
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            
            results.append({
                "id": record.id,
                "plate_number": plate_text,
                "confidence": float(confidence)
            })
        
        # Encode annotated image to base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        annotated_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "detections": results,
            "count": len(results),
            "annotated_image": annotated_b64
        }
    
    finally:
        db.close()