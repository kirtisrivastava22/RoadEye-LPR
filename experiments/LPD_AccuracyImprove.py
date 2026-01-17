import cv2
import numpy as np
import torch
from ultralytics import YOLO
import pytesseract
import easyocr
import re
import os
from fuzzywuzzy import process

# Load the model only once when the module is imported
model = YOLO("new_runs/detect/train2/weights/best.pt")

# List of valid Indian state codes for correction
VALID_STATE_CODES = ["MH", "DL", "KA", "TN", "GJ", "UP", "RJ", "WB", "MP", "PN", "HP", "CH", "BR", "AR", "AP", "AS", "GA", "DN", "HR", "JK", "KL", "LD", "MN", "MZ", "NL", "ML", "OR", "SK", "TR"]

# Initialize EasyOCR reader only once
reader = easyocr.Reader(['en'])

def detect_license_plate(image_path):
    """Detect license plate in the image and return cropped plate and annotated image"""
    # Ensure the image exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Run detection
    results = model.predict(source=image_path, conf=0.25)
    img = cv2.imread(image_path)
    
    # Check if image was loaded correctly
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    best_plate = None
    best_confidence = 0
    best_box = None

    for result in results:
        if len(result.boxes) == 0:
            continue
            
        for i, box in enumerate(result.boxes):
            confidence = float(box.conf[0])
            if confidence > best_confidence:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Ensure coordinates are valid
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)
                
                # Ensure cropped plate has positive dimensions
                if x2 <= x1 or y2 <= y1:
                    continue
                    
                cropped_plate = img[y1:y2, x1:x2]
                best_plate = cropped_plate
                best_confidence = confidence
                best_box = (x1, y1, x2, y2)

    # If no plate was detected or best_box is None
    if best_plate is None or best_box is None:
        return None, img

    # Draw rectangle on the original image
    x1, y1, x2, y2 = best_box
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    return best_plate, img

def preprocess_plate(image):
    """Apply preprocessing to enhance plate readability"""
    preprocessed_images = []
    
    # Original image
    preprocessed_images.append(image)
    
    # Resize for better OCR (2x)
    height, width = image.shape[:2]
    resized = cv2.resize(image, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
    preprocessed_images.append(resized)
    
    # Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    preprocessed_images.append(gray)
    
    # Resized grayscale
    gray_resized = cv2.resize(gray, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
    preprocessed_images.append(gray_resized)
    
    # Binary thresholding
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    preprocessed_images.append(binary)
    
    # Adaptive thresholding
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY, 11, 2)
    preprocessed_images.append(adaptive)
    
    # Add more contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    preprocessed_images.append(enhanced)
    
    return preprocessed_images

def extract_text_with_easyocr(images):
    """Extract text using EasyOCR with different configurations"""
    all_texts = []
    
    for img in images:
        try:
            # Method 1: Normal reading
            results = reader.readtext(img, detail=0)
            if results:
                text = " ".join(results)
                all_texts.append(text)
            
            # Method 2: With allowlist
            results = reader.readtext(img, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', detail=0)
            if results:
                text = " ".join(results)
                all_texts.append(text)
                
            # Method 3: Different paragraph reading
            results = reader.readtext(img, paragraph=True, detail=0)
            if results:
                text = " ".join(results)
                all_texts.append(text)
                
        except Exception as e:
            print(f"EasyOCR error: {str(e)}")
    
    return all_texts

def extract_text_with_tesseract(images):
    """Extract text using Tesseract with different configurations"""
    all_texts = []
    
    for img in images:
        try:
            # Method 1: PSM 7 (Treat as single line)
            config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            text = pytesseract.image_to_string(img, config=config)
            if text.strip():
                all_texts.append(text.strip())
            
            # Method 2: PSM 8 (Treat as single word)
            config = "--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            text = pytesseract.image_to_string(img, config=config)
            if text.strip():
                all_texts.append(text.strip())
                
            # Method 3: PSM 6 (Assume uniform block of text)
            config = "--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            text = pytesseract.image_to_string(img, config=config)
            if text.strip():
                all_texts.append(text.strip())
                
            # Method 4: PSM 13 (Raw line)
            config = "--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            text = pytesseract.image_to_string(img, config=config)
            if text.strip():
                all_texts.append(text.strip())
                
        except Exception as e:
            print(f"Tesseract error: {str(e)}")
    
    return all_texts

def clean_and_format_text(text):
    """Clean and format the license plate text"""
    # Remove unwanted characters
    text = re.sub(r'[^A-Z0-9\s]', '', text.upper())
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # If text has no spaces, insert spaces based on standard Indian license plate format
    if ' ' not in text and len(text) >= 8:
        # Check if it starts with IND
        if text.startswith('IND'):
            # Format as IND XX XX XX XXXX (state code, district number, series, number)
            state_start = 3  # After IND
            formatted = "IND "
        else:
            state_start = 0
            formatted = ""
            
        # Add state code (2 characters)
        if len(text) >= state_start + 2:
            formatted += text[state_start:state_start+2] + " "
            
            # Add district number (1-2 characters)
            district_start = state_start + 2
            district_end = district_start + 2
            formatted += text[district_start:district_end] + " "
            
            # Add series (1-3 characters)
            series_start = district_end
            series_end = series_start + 2  # Assuming 2 characters for series
            formatted += text[series_start:series_end] + " "
            
            # Add number (remaining characters)
            number_start = series_end
            formatted += text[number_start:]
            
        return formatted
    
    return text

def select_best_text(texts):
    """Select the best text from multiple extracted texts"""
    if not texts:
        return ""
    
    # Filter out empty texts
    texts = [t for t in texts if t.strip()]
    if not texts:
        return ""
    
    # Sort by length (longer texts typically contain more information)
    texts.sort(key=len, reverse=True)
    
    # Look for texts matching standard Indian license plate format
    for text in texts:
        # Check for patterns like "MH 01 AV 8866" or "IND MH 01 AV 8866"
        if re.search(r'(?:IND\s+)?[A-Z]{2}\s+\d{1,2}\s+[A-Z]{1,3}\s+\d{1,4}', text):
            return text
    
    # If no match found, use the longest text
    longest_text = texts[0]
    
    # Ensure it's properly formatted
    return clean_and_format_text(longest_text)

def main(image_path):
    """Main function to process license plate image"""
    try:
        # Step 1: Detect and crop license plate
        plate, detected_image = detect_license_plate(image_path)
        
        if plate is None:
            print("No license plate detected")
            # Return with a clear message instead of None
            return None, detected_image, "No plate detected", ""
        
        # Step 2: Preprocess plate for better recognition
        preprocessed_plates = preprocess_plate(plate)
        
        # Step 3: Extract text using multiple methods
        easyocr_texts = extract_text_with_easyocr(preprocessed_plates)
        tesseract_texts = extract_text_with_tesseract(preprocessed_plates)
        
        # Combine all texts
        all_texts = easyocr_texts + tesseract_texts
        
        # Step 4: Select the best text
        plate_text = select_best_text(all_texts)
        
        if not plate_text:
            print("No text could be extracted from the plate")
            return plate, detected_image, "No text detected", ""
        
        # Step 5: Clean and format the text
        formatted_text = clean_and_format_text(plate_text)
        
        print(f"Detected plate text: {formatted_text}")
        
        # Return empty string for validation_result
        return plate, detected_image, formatted_text, ""
        
    except Exception as e:
        print(f"Error in license plate processing: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return a more graceful error that won't cause the frontend to crash
        return None, None, "Error occurred", ""