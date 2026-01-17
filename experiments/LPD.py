import cv2
import numpy as np
import torch
from ultralytics import YOLO
import pytesseract
import easyocr
import re
import matplotlib.pyplot as plt
from fuzzywuzzy import process

model = YOLO("new_runs/detect/train2/weights/best.pt")

def detect_license_plate(image_path):
    results = model.predict(source=image_path, conf=0.5)
    img = cv2.imread(image_path)

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0]) 
            cropped_plate = img[y1:y2, x1:x2] 

            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            return cropped_plate, img  

    return None, img

def preprocess_plate(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  
    gray = cv2.GaussianBlur(gray, (3, 3), 0)  
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )


    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return processed

def extract_text_easyocr(plate):
    reader = easyocr.Reader(['en'])  
    results = reader.readtext(plate, detail=0) 
    text = " ".join(results) if results else "N/A"
    clean_text = "".join(re.findall(r"[A-Z0-9\s]", text)).strip()

    return clean_text


def extract_text_tesseract(plate):
    text = pytesseract.image_to_string(plate, config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    return text.strip()

def validate_license(text):
    pattern = r'^(?:IND\s?)?[A-Z]{2}\s?\d{2}\s?[A-Z]{1,3}\s?\d{4}$'
    is_valid = bool(re.match(pattern, text))

    if is_valid:
        if text.startswith("IND"):
            return "✅ Valid License Plate"
        else:
            return "✅ Valid License Plate (Update Recommended Acc to Gov. : Addition of 'IND')"
    return "❌ Invalid License Plate"

VALID_STATE_CODES = ["MH", "DL", "KA", "TN", "GJ", "UP", "RJ", "WB", "MP", "PN","HP","MP","CH","BR","AR","AP","AS","GA","DN","HR","JK","KL","LD","MN","MZ","NL","ML","OR","SK","TR"]

def correct_state_code(text):
    words = text.split()
    if len(words) > 0:
        best_match, score = process.extractOne(words[0], VALID_STATE_CODES)
        if score > 80:  
            words[0] = best_match
    return " ".join(words)


def main(image_path):
    plate, detected_image = detect_license_plate(image_path)
    if plate is not None:
        processed_plate = preprocess_plate(plate)
        plate_number = extract_text_easyocr(processed_plate)
        if len(plate_number) < 6:  
            plate_number = extract_text_tesseract(processed_plate)
        plate_number = correct_state_code(plate_number)
        validation_result = validate_license(plate_number)
        return plate, detected_image, plate_number, validation_result
    
    return None, None, None, None