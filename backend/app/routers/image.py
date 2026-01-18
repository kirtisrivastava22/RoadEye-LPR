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
    
    # Process the image
    plate_crop, annotated_image, plate_text, confidence = process_license_plate(image)
    
    results = []
    db = SessionLocal()
    
    try:
        # Debug: Print what we got from process_license_plate
        print(f"Debug - plate_text: {plate_text}, type: {type(plate_text)}, confidence: {confidence}")
        
        # Check if plate_text is not None, not empty string, and confidence is reasonable
        if plate_text and str(plate_text).strip() and confidence > 0:
            plate_text_clean = str(plate_text).strip()
            
            # Generate timestamp and filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{timestamp}_{plate_text_clean}.jpg"
            abs_image_path = os.path.join(UPLOAD_DIR, image_filename)
            
            # Save the annotated image
            cv2.imwrite(abs_image_path, annotated_image)
            
            # Create database record
            record = Detection(
                plate_number=plate_text_clean,
                confidence=float(confidence),
                source="image",
                image_path=f"/uploads/images/{image_filename}"
            )
            
            db.add(record)
            db.commit()
            db.refresh(record)
            
            print(f"Saved to DB - ID: {record.id}, Plate: {record.plate_number}")
            
            results.append({
                "id": record.id,
                "plate_number": record.plate_number,
                "confidence": record.confidence
            })
        else:
            print(f"Skipped saving - plate_text: '{plate_text}', confidence: {confidence}")
        
        # Encode annotated image to base64
        _, buffer = cv2.imencode(".jpg", annotated_image)
        annotated_b64 = base64.b64encode(buffer).decode("utf-8")
        
        return {
            "detections": results,
            "count": len(results),
            "annotated_image": annotated_b64
        }
        
    except Exception as e:
        print(f"Error in detect_image: {e}")
        db.rollback()
        raise
    finally:
        db.close()