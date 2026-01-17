from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import image, video, webcam, history
from app.database import engine
from app.models import Detection
import os
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

app = FastAPI(title="RoadEye-LPR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Detection.__table__.create(bind=engine, checkfirst=True)

@app.get("/")
def health_check():
    return {"status": "API running"}

app.include_router(image.router, prefix="/detect", tags=["Image"])
app.include_router(video.router, prefix="/detect", tags=["Video"])
app.include_router(webcam.router, tags=["WebSocket"])
app.include_router(history.router, prefix="/history", tags=["History"])
