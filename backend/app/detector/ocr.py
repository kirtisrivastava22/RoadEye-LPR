import cv2
import numpy as np
from app.detector.plate_postprocess import apply_plate_syntax

_easy_reader = None  # global singleton

def get_easy_reader():
    global _easy_reader
    if _easy_reader is None:
        import easyocr
        print("[LAZY LOAD] Initializing EasyOCR...")
        _easy_reader = easyocr.Reader(['en'], gpu=False)
    return _easy_reader


class PlateOCR:
    def __init__(self):
        # IMPORTANT: do NOTHING heavy here
        print("[INIT] PlateOCR lightweight init")

    def read_plate(self, plate_img: np.ndarray):
        if plate_img is None or plate_img.size == 0:
            return "", 0.0

        plate_img = self._preprocess(plate_img)

        reader = get_easy_reader()
        results = reader.readtext(plate_img)

        if not results:
            return "", 0.0

        results.sort(key=lambda x: x[2], reverse=True)
        text = self._clean(results[0][1])
        conf = float(results[0][2])
        return text, conf

    def _clean(self, text):
        text = "".join(c for c in text.upper() if c.isalnum())
        return apply_plate_syntax(text, country="IN")

    def _preprocess(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        if gray.mean() < 70:
            gray = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

        h = gray.shape[0]
        if h < 40:
            scale = 40 / h
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        gray = cv2.equalizeHist(gray)

        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
