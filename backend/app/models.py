# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Detection(Base):
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, index=True)
    confidence = Column(Float)
    source = Column(String)  # "image", "video", or "live"
    timestamp = Column(DateTime, default=datetime.utcnow)
    image_path = Column(String, nullable=True)  # Path to saved image
    video_timestamp = Column(Float, nullable=True)  # For video detections
    
    def __repr__(self):
        return f"<Detection(plate={self.plate_number}, conf={self.confidence:.2f}, source={self.source})>"