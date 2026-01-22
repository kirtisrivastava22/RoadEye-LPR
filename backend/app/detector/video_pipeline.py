import cv2
from ultralytics import YOLO
import os
import logging
from collections import defaultdict
from app.detector.ocr import PlateOCR
import torch
torch.set_grad_enabled(False)

_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = PlateOCR()
    return _ocr_engine

# Prevent multiprocessing issues on Windows
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(
    BASE_DIR,
    "new_runs",
    "detect",
    "train",
    "weights",
    "best.pt"
)
# Initialize models as None
_model = None

plate_buffer = defaultdict(list)

def get_model():
    global _model
    if _model is None:
        print(f"[INIT] Loading YOLO model from {MODEL_PATH}")
        _model = YOLO(MODEL_PATH)
    return _model

def detect_license_plate(image):
    """Enhanced detection with debugging"""
    model = get_model()
    
    if image is None or image.size == 0:
        print("[ERROR] Invalid input image")
        return None, image, 0.0
    
    print(f"[DEBUG] Processing image shape: {image.shape}")
    
    results = model.predict(
    source=image,
    imgsz=640,
    conf=0.15,
    iou=0.45,
    device="cpu",
    half=False,
    verbose=False
    )

    
    if not results or len(results) == 0:
        print("[DEBUG] No results returned from model")
        return None, image, 0.0
    
    result = results[0]
    print(f"[DEBUG] Total detections: {len(result.boxes)}")
    
    if len(result.boxes) == 0:
        print("[DEBUG] No boxes detected")
        return None, image, 0.0
    
    best_plate = None
    best_confidence = 0
    best_box = None
    
    for i, box in enumerate(result.boxes):
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        print(f"[DEBUG] Box {i}: conf={confidence:.3f}, coords=({x1},{y1},{x2},{y2})")
        
        if x2 <= x1 or y2 <= y1:
            continue
        
        width = x2 - x1
        height = y2 - y1
        if width < 20 or height < 10:
            continue
        
        if confidence > best_confidence:
            cropped_plate = image[y1:y2, x1:x2]
            if cropped_plate.size > 0:
                best_plate = cropped_plate
                best_confidence = confidence
                best_box = (x1, y1, x2, y2)
    
    if best_plate is None:
        print("[DEBUG] No valid plates found after filtering")
        return None, image, 0.0
    
    x1, y1, x2, y2 = best_box
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(image, f"{best_confidence:.2f}", (x1, y1-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    print(f"[SUCCESS] Plate detected with confidence {best_confidence:.3f}")
    return best_plate, image, best_confidence


def extract_text_with_easyocr(image):
    """Extract text from license plate image using EasyOCR"""
    ocr = get_ocr_engine()
    
    if image is None or image.size == 0:
        print("[DEBUG] Invalid image for OCR")
        return []
    
    print(f"[DEBUG] OCR input shape: {image.shape}")
    
    # EasyOCR works better with grayscale for license plates
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Enhance image
    h, w = gray.shape[:2]
    
    # Resize if too small
    if h < 32:
        scale = 32 / h
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        print(f"[DEBUG] Resized to: {gray.shape}")
    
    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    try:
        # EasyOCR expects RGB
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
        
        # Run OCR
        results = ocr.readtext(enhanced_rgb, detail=1)
        
        if not results:
            print("[DEBUG] OCR returned no results")
            return []
        
        texts = []
        for detection in results:
            bbox, text, conf = detection
            print(f"[DEBUG] OCR detected: '{text}' (confidence: {conf:.3f})")
            if conf > 0.3:  # Filter low confidence
                texts.append(text)
        
        return texts
        
    except Exception as e:
        print(f"[ERROR] OCR exception: {e}")
        import traceback
        traceback.print_exc()
        return []


def process_license_plate(image):
    print("[PIPELINE] Processing frame")
    """Process single image for license plate detection and OCR"""
    plate, detected_image, confidence = detect_license_plate(image)
    
    if plate is None:
        return None, detected_image, None, 0.0
    
    # ocr_texts = extract_text_with_easyocr(plate)
    
    # if not ocr_texts:
    #     return None, detected_image, None, confidence
    ocr = get_ocr_engine()
    text, conf = ocr.read_plate(plate)
    formatted_text = text
    
    cv2.putText(detected_image, formatted_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    
    print(f"[RESULT] Plate: {formatted_text}")
    return plate, detected_image, formatted_text, confidence


def process_video(input_path, output_path):
    """Process video file for license plate detection"""
    cap = cv2.VideoCapture(input_path)
    output_path = output_path.rsplit('.', 1)[0] + '.mp4'
    
    if not cap.isOpened():
        print(f"[ERROR] Could not open video file: {input_path}")
        return False, []
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    detected_plates = set()
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        try:
            _, annotated_frame, ocr_text, _ = process_license_plate(frame)
            if annotated_frame is None:
                annotated_frame = frame
        except Exception as e:
            print(f"[ERROR] Frame {frame_count} failed: {e}")
            annotated_frame = frame
            ocr_text = None
        
        if (annotated_frame.shape[1] != frame_width) or (annotated_frame.shape[0] != frame_height):
            annotated_frame = cv2.resize(annotated_frame, (frame_width, frame_height))
        
        out.write(annotated_frame)
        if ocr_text:
            plate_buffer[ocr_text].append(ocr_text)

            if len(plate_buffer[ocr_text]) >= 3:
                detected_plates.add(ocr_text)
        
        if frame_count % 30 == 0:
            print(f"[INFO] Processed frame {frame_count} - OCR: {ocr_text}")
        

        frame_count += 1
    
    cap.release()
    out.release()
    
    print(f"[SUCCESS] Video processing complete: {output_path}")
    print(f"[INFO] Detected plates: {detected_plates}")
    return True, list(detected_plates)