from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import image, history, video
from app.database import engine
from app.models import Base
import os

Base.metadata.create_all(bind=engine)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
IMAGE_DIR = os.path.join(UPLOAD_DIR, "images")
VIDEO_DIR = os.path.join(UPLOAD_DIR, "videos")

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

app = FastAPI(title="RoadEye LPR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


app.include_router(image.router, prefix="/detect", tags=["Detection"])
app.include_router(video.router, prefix="/ws", tags=["WebSocket"])
app.include_router(history.router, prefix="/history", tags=["History"])

@app.get("/")
async def root():
    return {
        "message": "RoadEye LPR API",
        "version": "1.0.0",
        "endpoints": {
            "image_detection": "/detect/image",
            "history": "/history/"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
