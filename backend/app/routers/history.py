# app/routers/history.py
from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.database import SessionLocal
from app.models import Detection
import os

router = APIRouter()

@router.get("/")
def get_history():
    """Get all detection history records"""
    db = SessionLocal()
    try:
        records = db.query(Detection).order_by(Detection.timestamp.desc()).all()
        
        return [
            {
                "id": r.id,
                "plate_number": r.plate_number,
                "confidence": r.confidence,
                "timestamp": r.timestamp.isoformat(),
                "source": r.source,
                "image_path": r.image_path if hasattr(r, 'image_path') else None
            }
            for r in records
        ]
    finally:
        db.close()


@router.delete("/{record_id}")
def delete_record(record_id: int):
    """Delete a specific detection record"""
    db = SessionLocal()
    try:
        record = db.query(Detection).filter(Detection.id == record_id).first()
        if not record:
            return {"error": "Record not found"}
        
        # Delete associated image file if exists
        if hasattr(record, 'image_path') and record.image_path:
            image_path = record.image_path.lstrip('/')
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.delete(record)
        db.commit()
        return {"success": True, "id": record_id}
    finally:
        db.close()


@router.get("/clear")
def clear_all_history():
    """Clear all detection records"""
    db = SessionLocal()
    try:
        count = db.query(Detection).delete()
        db.commit()
        return {"success": True, "deleted": count}
    finally:
        db.close()