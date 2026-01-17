# from fastapi import APIRouter, WebSocket
# import base64, cv2, numpy as np

# from app.detector.detector import PlateDetector
# from app.database import SessionLocal
# from app.models import Detection

# router = APIRouter()
# detector = PlateDetector("../../new_runs/detect/train2/weights/best.pt")
# CONF_THRESHOLD = 0.2

# @router.websocket("/ws/video")
# async def video_stream(websocket: WebSocket):
#     await websocket.accept()
#     db = SessionLocal()

#     try:
#         while True:
#             data = await websocket.receive_text()

#             if "," in data:
#                 data = data.split(",")[1]

#             img_bytes = base64.b64decode(data)
#             np_img = np.frombuffer(img_bytes, np.uint8)
#             frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

#             detections = detector.detect(frame)

#             for det in detections:
#                 if det["confidence"] < CONF_THRESHOLD:
#                     continue

#                 x1, y1, x2, y2 = map(int, det["box"])
#                 cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

#                 new_det = Detection(
#                     plate_number="UNKNOWN",
#                     confidence=det["confidence"],
#                     source="live"
#                 )
#                 db.add(new_det)

#             db.commit()

#             # 🔥 Send back processed frame instead of JSON
#             await websocket.send_bytes(cv2.imencode(".jpg", frame)[1].tobytes())

#     except Exception as e:
#         print("WebSocket closed:", e)

#     finally:
#         db.close()
#         try:
#             await websocket.close()
#         except:
#             pass
