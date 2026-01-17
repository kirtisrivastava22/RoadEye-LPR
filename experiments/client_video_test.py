import cv2
import base64
import json
import websocket

WS_URL = "ws://127.0.0.1:8000/ws/video"

def on_open(ws):
    print("WebSocket connected")

    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        _, buffer = cv2.imencode(".jpg", frame)
        frame_b64 = base64.b64encode(buffer).decode("utf-8")

        ws.send(frame_b64)

        cv2.imshow("Client Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    ws.close()

def on_message(ws, message):
    detections = json.loads(message)
    if detections:
        print("Detections:", detections)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

ws = websocket.WebSocketApp(
    WS_URL,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()
