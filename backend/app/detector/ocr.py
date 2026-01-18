import easyocr
import numpy as np

class PlateOCR:
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)
    
    def read_plate(self, plate_img: np.ndarray) -> tuple[str, float]:
        """
        Read plate text and return (text, confidence)
        Returns: (cleaned_text, confidence_score)
        """
        print(f"[DEBUG] OCR input shape: {plate_img.shape}")
        
        results = self.reader.readtext(plate_img)
        
        if not results:
            print("[DEBUG] OCR found no text")
            return "", 0.0
        
        # Sort by confidence and get the best result
        results.sort(key=lambda x: x[2], reverse=True)
        best_result = results[0]
        
        # Extract text and confidence
        text = best_result[1]
        confidence = float(best_result[2])
        
        print(f"[DEBUG] OCR detected: '{text}' (confidence: {confidence:.3f})")
        
        # Clean the text
        cleaned_text = self.clean_text(text)
        
        print(f"[DEBUG] Cleaned text: '{cleaned_text}'")
        
        return cleaned_text, confidence
    
    def clean_text(self, text: str) -> str:
        """Clean OCR text to extract valid plate number"""
        if not text:
            return ""
        
        # Remove common OCR artifacts and clean
        cleaned = text.strip()
        cleaned = cleaned.replace('[', '').replace(']', '')
        cleaned = cleaned.replace('(', '').replace(')', '')
        cleaned = cleaned.replace('{', '').replace('}', '')
        cleaned = cleaned.replace(',', '').replace('.', '')
        cleaned = cleaned.replace(' ', '').replace('-', '')
        cleaned = cleaned.replace('|', 'I').replace('!', '1')
        
        # Common OCR corrections
        # cleaned = cleaned.replace('O', '0')  # Uncomment if needed
        
        cleaned = cleaned.upper()
        
        return cleaned
    
    def read_plate_all_results(self, plate_img: np.ndarray) -> list:
        """
        Return all OCR results for debugging
        Returns: list of (text, confidence) tuples
        """
        results = self.reader.readtext(plate_img)
        
        return [(r[1], float(r[2])) for r in results]