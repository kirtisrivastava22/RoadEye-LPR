from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.detector.video_pipeline import process_license_plate
from app.database import SessionLocal
from app.models import Detection
from datetime import datetime

import cv2
import numpy as np
import base64
import json
import time
from asyncio import get_running_loop
from functools import partial
from collections import deque

router = APIRouter()

CONF_THRESHOLD = 0.2
DEDUP_WINDOW_SEC = 5     
MAX_IN_MEMORY_EVENTS = 500

history_buffer = deque(maxlen=MAX_IN_MEMORY_EVENTS)
recent_plates = {}  


def encode_frame(frame):
    _, buffer = cv2.imencode(".jpg", frame)
    return base64.b64encode(buffer).decode("utf-8")


from datetime import datetime

def save_video_detection(plate, confidence, video_ts):
    db = SessionLocal()
    try:
        record = Detection(
            plate_number=plate,
            confidence=confidence,
            source="video",
            timestamp=datetime.utcnow(),   
            video_timestamp=video_ts,     
            image_path=None
        )
        db.add(record)
        db.commit()
    finally:
        db.close()

def save_live_detection(plate, confidence):
    db = SessionLocal()
    try:
        record = Detection(
            plate_number=plate,
            confidence=confidence,
            source="live",
            timestamp=datetime.utcnow(), 
            video_timestamp=None,
            image_path=None
        )
        db.add(record)
        db.commit()
    finally:
        db.close()



def should_save_plate(plate):
    """Deduplicate plate saves to protect DB"""
    now = time.time()
    last_seen = recent_plates.get(plate)

    if last_seen and now - last_seen < DEDUP_WINDOW_SEC:
        return False

    recent_plates[plate] = now
    return True


# ===========================
# VIDEO FILE WEBSOCKET
# ===========================
@router.websocket("/video")
async def video_stream_ws(ws: WebSocket):
    await ws.accept()

    loop = get_running_loop()
    last_timestamp = 0.0

    try:
        while True:
            msg = await ws.receive()
            await ws.send_json({"type": "status", "message": "processing"})
            # ---------- TEXT ----------
            if msg.get("text"):
                try:
                    payload = json.loads(msg["text"])

                    if payload.get("type") == "ping":
                        continue

                    if payload.get("type") == "frame_meta":
                        last_timestamp = float(payload.get("timestamp", last_timestamp))
                        continue
                except Exception:
                    continue

            # ---------- IMAGE ----------
            if not msg.get("bytes"):
                continue

            nparr = np.frombuffer(msg["bytes"], np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            plate_img, annotated, plate_text, confidence = await loop.run_in_executor(
                None,
                partial(process_license_plate, frame)
            )

            if confidence < CONF_THRESHOLD:
                plate_text = None

            # ---------- SAVE TO DB (metadata only) ----------
            if plate_text and should_save_plate(plate_text):
                save_video_detection(
                    plate=plate_text.strip(),
                    confidence=confidence,
                    video_ts=last_timestamp
                )

            # ---------- IN-MEMORY BUFFER ----------
            history_buffer.append({
                "plate": plate_text,
                "timestamp": last_timestamp,
                "confidence": confidence,
                "source": "video"
            })

            # ---------- SEND BACK ----------
            try:
                await ws.send_json({
                    "frame": encode_frame(annotated),
                    "plate": plate_text,
                    "confidence": confidence,
                    "timestamp": last_timestamp
                })
            except Exception:
                break  # client disconnected


    except WebSocketDisconnect:
        print("[INFO] Video WS disconnected")

    except Exception as e:
        print("[ERROR]", e)
        import traceback
        traceback.print_exc()


# ===========================
# LIVE WEBCAM WEBSOCKET
# ===========================
@router.websocket("/webcam")
async def webcam_ws(ws: WebSocket):
    await ws.accept()
    loop = get_running_loop()

    try:
        while True:
            msg = await ws.receive()
            await ws.send_json({"type": "status", "message": "processing"})

            if msg.get("text"):
                try:
                    payload = json.loads(msg["text"])
                    if payload.get("type") == "ping":
                        continue
                except Exception:
                    continue

            if not msg.get("bytes"):
                continue

            nparr = np.frombuffer(msg["bytes"], np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            plate_img, annotated, plate_text, confidence = await loop.run_in_executor(
                None,
                partial(process_license_plate, frame)
            )

            if confidence < CONF_THRESHOLD:
                plate_text = None

            if plate_text and should_save_plate(plate_text):
                save_live_detection(
                    plate=plate_text.strip(),
                    confidence=confidence
                )

            history_buffer.append({
                "plate": plate_text,
                "timestamp": time.time(),
                "confidence": confidence,
                "source": "live"
            })

            await ws.send_json({
                "frame": encode_frame(annotated),
                "plate": plate_text,
                "confidence": confidence,
                "timestamp": time.time()
            })

    except WebSocketDisconnect:
        print("[INFO] Webcam WS disconnected")
