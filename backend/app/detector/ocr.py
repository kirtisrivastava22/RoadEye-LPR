import numpy as np
import cv2
import re
from app.detector.plate_postprocess import apply_plate_syntax


try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

import easyocr


class PlateOCR:
    def __init__(self):
        print("[INIT] PlateOCR")

        # EasyOCR (always available)
        self.easy = easyocr.Reader(['en'], gpu=False)

        # PaddleOCR (optional)
        self.paddle = None
        if PADDLE_AVAILABLE:
            try:
                self.paddle = PaddleOCR(
                    use_angle_cls=True,
                    lang='en'
                )
                print("[INIT] PaddleOCR loaded")
            except Exception as e:
                print("[WARN] PaddleOCR failed, falling back to EasyOCR:", e)
                self.paddle = None

    def read_plate(self, plate_img: np.ndarray) -> str:
        if plate_img is None or plate_img.size == 0:
            return ""

        plate_img = self._preprocess(plate_img)

        # 1️⃣ PaddleOCR first
        if self.paddle:
            text = self._read_paddle(plate_img)
            if text:
                print(f"[OCR:PADDLE] {text}")
                return text

        # 2️⃣ EasyOCR fallback
        text = self._read_easy(plate_img)
        if text:
            print(f"[OCR:EASY] {text}")
            return text

        return ""

    def _read_paddle(self, img):
        try:
            result = self.paddle.predict(img) 
        except Exception as e:
            print("[ERROR] PaddleOCR failed:", e)
            return ""

        if not result or not result[0]:
            return ""

        best = max(result[0], key=lambda x: x[1][1])
        return self._clean(best[1][0])


    def _read_easy(self, img):
        results = self.easy.readtext(img)
        if not results:
            return ""

        results.sort(key=lambda x: x[2], reverse=True)
        return self._clean(results[0][1])

    def _clean(self, text: str) -> str:
        text = text.upper()
        text = text.upper()
        text = "".join(c for c in text if c.isalnum())
        text = apply_plate_syntax(text, country="IN")
        return text


    def _preprocess(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        h, w = gray.shape
        if h < 40:
            scale = 40 / h
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        gray = cv2.equalizeHist(gray)

        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
