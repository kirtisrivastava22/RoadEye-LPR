# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import image, history, video
from app.database import engine
from app.models import Base
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Create upload directories
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)

app = FastAPI(title="RoadEye LPR API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (uploaded images)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
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
            "video_stream": "/ws/video_stream",
            "history": "/history/"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1  # Single worker for Windows compatibility
    )