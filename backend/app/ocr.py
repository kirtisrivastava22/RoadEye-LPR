import easyocr
import numpy as np

class PlateOCR:
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)

    def read_plate(self, plate_img: np.ndarray) -> str:
        results = self.reader.readtext(plate_img)
        if not results:
            return ""

        # Take the text with highest confidence
        results.sort(key=lambda x: x[2], reverse=True)
        text = results[0][1]

        # Basic cleanup
        text = text.replace(" ", "").upper()
        return text
