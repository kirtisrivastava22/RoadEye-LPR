import cv2
from paddleocr import PaddleOCR
from ultralytics import YOLO

ocr = PaddleOCR(use_angle_cls=True, lang='en')
model = YOLO("../../YOLO_MODELS/detect/train/weights/best.pt")

def detect_license_plate(image):
    results = model.predict(source=image, conf=0.25)
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
                if x2 <= x1 or y2 <= y1:
                    continue
                cropped_plate = image[y1:y2, x1:x2]
                best_plate = cropped_plate
                best_confidence = confidence
                best_box = (x1, y1, x2, y2)

    if best_plate is None:
        return None, image

    x1, y1, x2, y2 = best_box
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return best_plate, image

def extract_text_with_paddleocr(image):
    if len(image.shape) == 2 or image.shape[2] == 1:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    image = cv2.convertScaleAbs(image, alpha=1.5, beta=0)
    result = ocr.ocr(image, cls=True)

    if not result or not result[0]:
        print("[DEBUG] OCR returned no results")
        return []

    texts = [line[1][0] for line in result[0]]
    print(f"[DEBUG] OCR Detected Texts: {texts}")
    return texts

def process_license_plate(image):
    plate, detected_image = detect_license_plate(image)
    if plate is None:
        return None, detected_image, None

    ocr_texts = extract_text_with_paddleocr(plate)
    if not ocr_texts:
        return None, detected_image, None

    formatted_text = " ".join(ocr_texts)
    cv2.putText(detected_image, formatted_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    print(f"[RESULT] Plate: {formatted_text}")
    return plate, detected_image, formatted_text


def process_video(input_path, output_path):
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
    valid_frames_written = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        try:
            _, annotated_frame, ocr_text = process_license_plate(frame)
            if annotated_frame is None:
                annotated_frame = frame
        except Exception as e:
            print(f"[ERROR] Frame {frame_count} failed: {e}")
            annotated_frame = frame
            ocr_text = None

        if (annotated_frame.shape[1] != frame_width) or (annotated_frame.shape[0] != frame_height):
            annotated_frame = cv2.resize(annotated_frame, (frame_width, frame_height))

        out.write(annotated_frame)
        valid_frames_written += 1

        if ocr_text and ocr_text.strip().lower() != "no plate detected":
            detected_plates.add(ocr_text.strip())

        if frame_count % 30 == 0:
            print(f"[INFO] Processed frame {frame_count} - OCR: {ocr_text}")
        frame_count += 1

    cap.release()
    out.release()

    if valid_frames_written == 0:
        print("[ERROR] No valid frames were written. Output may be corrupt.")
        return False, []

    print(f"[SUCCESS] Video processing complete: {output_path}")
    return True, list(detected_plates)