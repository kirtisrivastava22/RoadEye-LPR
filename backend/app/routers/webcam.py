from fastapi import APIRouter, WebSocket
import base64, cv2, numpy as np

from app.detector.detector import PlateDetector

router = APIRouter()
detector = PlateDetector("yolov8n.pt")
CONF_THRESHOLD = 0.2

@router.websocket("/ws/video")
async def video_stream(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            img_bytes = base64.b64decode(data)
            np_img = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

            detections = detector.detect(frame)

            response = []
            for det in detections:
                if det["confidence"] < CONF_THRESHOLD:
                    continue
                response.append({
                    "bbox": det["bbox"],
                    "confidence": det["confidence"]
                })

            await websocket.send_json(response)

    except Exception as e:
        print("WebSocket closed:", e)
