import cv2
from ultralytics import YOLO
from collections import defaultdict
from app.detector.ocr import PlateOCR

ocr_engine = PlateOCR()
plate_buffer = defaultdict(int)


class PlateDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def detect(self, image, conf_thresh=0.25):
        results = self.model.predict(image, imgsz=960, conf=conf_thresh, verbose=False)
        detections = []

        if not results:
            return detections

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                if conf < conf_thresh:
                    continue

                if x2 <= x1 or y2 <= y1:
                    continue

                crop = image[y1:y2, x1:x2]
                if crop.size == 0:
                    continue

                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "det_conf": conf,
                    "crop": crop
                })

        return detections


def process_license_plate(image, detector: PlateDetector):
    detections = detector.detect(image)
    results = []

    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        plate_img = det["crop"]

        text, ocr_conf = ocr_engine.read_plate(plate_img)

        if not text or ocr_conf < 0.4:
            continue

        # Temporal stabilisation (video-safe)
        plate_buffer[text] += 1
        if plate_buffer[text] < 2:
            continue

        cv2.rectangle(image, (x1,y1),(x2,y2),(0,255,0),2)
        cv2.putText(
            image,
            f"{text} ({ocr_conf:.2f})",
            (x1, y1-8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,255,0),
            2
        )

        results.append({
            "plate": text,
            "det_conf": det["det_conf"],
            "ocr_conf": ocr_conf,
            "bbox": det["bbox"]
        })

    return image, results
