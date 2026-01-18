import numpy as np
import cv2
from app.detector.plate_postprocess import apply_plate_syntax

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

import easyocr


def plate_quality_score(crop):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast = gray.std()
    h, w = gray.shape

    return (
        0.4 * min(sharpness / 200, 1.0) +
        0.4 * min(contrast / 50, 1.0) +
        0.2 * min((h * w) / (120 * 40), 1.0)
    )


class PlateOCR:
    def __init__(self):
        print("[INIT] PlateOCR")

        self.easy = easyocr.Reader(['en'], gpu=False)
        self.paddle = None

        if PADDLE_AVAILABLE:
            try:
                self.paddle = PaddleOCR(use_angle_cls=True, lang='en')
                print("[INIT] PaddleOCR loaded")
            except Exception as e:
                print("[WARN] PaddleOCR failed:", e)

    def read_plate(self, plate_img: np.ndarray):
        if plate_img is None or plate_img.size == 0:
            return "", 0.0

        plate_img = self._preprocess(plate_img)

        #  PaddleOCR first
        if self.paddle:
            text, conf = self._read_paddle(plate_img)
            if text:
                print(f"[OCR:PADDLE] {text} ({conf:.2f})")
                return text, conf

        #  EasyOCR fallback
        text, conf = self._read_easy(plate_img)
        if text:
            print(f"[OCR:EASY] {text} ({conf:.2f})")
            return text, conf

        return "", 0.0


    def _read_paddle(self, img):
        try:
            result = self.paddle.predict(img)
        except Exception as e:
            print("[ERROR] PaddleOCR failed:", e)
            return "", 0.0

        if not result or not result[0]:
            return "", 0.0

        best = max(result[0], key=lambda x: x[1][1])
        text = self._clean(best[1][0])
        conf = float(best[1][1])
        return text, conf

    def _read_easy(self, img):
        results = self.easy.readtext(img)
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

        if gray.mean() < 70:  # Night footage
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
