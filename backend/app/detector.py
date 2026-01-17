from ultralytics import YOLO
import numpy as np
import cv2

class PlateDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def detect(self, image):
        results = self.model(image)
        detections = []

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                plate_crop = image[y1:y2, x1:x2]

                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": conf,
                    "plate_crop": plate_crop
                })

        return detections
