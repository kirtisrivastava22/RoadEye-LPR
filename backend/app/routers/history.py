from fastapi import APIRouter
from app.database import SessionLocal
from app.models import Detection

router = APIRouter()

@router.get("/")
def get_history():
    db = SessionLocal()
    records = db.query(Detection).order_by(Detection.timestamp.desc()).all()
    db.close()

    return [
        {
            "id": r.id,
            "plate_number": r.plate_number,
            "confidence": r.confidence,
            "timestamp": r.timestamp,
            "source": r.source
        }
        for r in records
    ]
