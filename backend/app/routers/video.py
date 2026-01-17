# ws_video.py or video.py (your WebSocket handler)
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.detector.video_pipeline import process_license_plate
import cv2
import numpy as np
import base64
import json

router = APIRouter()

def encode_frame(frame):
    """Convert OpenCV frame to base64 for frontend"""
    _, buffer = cv2.imencode(".jpg", frame)
    return base64.b64encode(buffer).decode("utf-8")

@router.websocket("/video")
async def video_stream_ws(ws: WebSocket):
    await ws.accept()
    detected_plates = set()
    
    try:
        while True:
            # Receive data with timestamp
            data = await ws.receive_bytes()
            
            # Try to parse timestamp from the beginning
            try:
                # Find the newline separator
                newline_idx = data.find(b'\n')
                if newline_idx > 0:
                    # Extract metadata and image data
                    metadata_bytes = data[:newline_idx]
                    image_bytes = data[newline_idx + 1:]
                    
                    # Parse metadata
                    metadata = json.loads(metadata_bytes.decode('utf-8'))
                    video_timestamp = metadata.get('timestamp', 0)
                else:
                    # No metadata, just image
                    image_bytes = data
                    video_timestamp = 0
            except:
                # Fallback if parsing fails
                image_bytes = data
                video_timestamp = 0
            
            # Decode image
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                continue
            
            # Process frame
            _, annotated_frame, ocr_text, confidence = process_license_plate(frame)
            
            if ocr_text:
                detected_plates.add(ocr_text.strip())
            
            frame_b64 = encode_frame(annotated_frame)
            
            # Send response with timestamp
            await ws.send_json({
                "frame": frame_b64,
                "plate": ocr_text,
                "confidence": confidence,
                "timestamp": video_timestamp  # Send back the video timestamp
            })
            
    except WebSocketDisconnect:
        print("[INFO] WebSocket disconnected")
        print(f"[INFO] Total plates detected: {detected_plates}")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()