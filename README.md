# 🚗 RoadEye-LPR (License Plate Recognition System)

RoadEye-LPR is an **end-to-end License Plate Detection & Recognition application** built using **YOLO-based object detection**, **OCR**, **FastAPI backend**, and a **modern frontend**. It supports **multiple vehicle detection in a single image or video frame** and is designed with deployment and scalability in mind.

---

## ✨ Features

* 🔍 **Multi-vehicle & multi-plate detection** in a single image/frame
* 🧠 **YOLO-based License Plate Detection** (custom trained)
* 🔠 **OCR pipeline** for extracting plate text (beta)
* 🖼️ **Image & Video support**
* ⚡ **FastAPI backend** for high performance
* 🎨 **Frontend UI** with annotated results
* 💾 **Database logging** of detections
* 🚀 **Production-ready structure**

---

## 🗂️ Project Structure

```
RoadEye-LPR/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── detector/        # Detection & OCR pipelines
│   │   ├── routes/          # API routes
│   │   ├── models/          # Database models
│   │   └── main.py          # App entry point
│   └── requirements.txt
│
├── frontend/                # Frontend application
│
├── new_runs/
│   └── detect/
│       └── trainXX/
│           └── weights/
│               └── best.pt  # Final trained YOLO model
│
├── dataset/                 # (Optional) Training dataset
├── docs/                    # Documentation
├── README.md
└── .gitignore
```

---

## 🧠 Model Details

* **Detector**: YOLO (custom trained for license plates)
* **Supports**: Multiple plates per image
* **Confidence thresholding** applied
* **Best model only** is used in production (`best.pt`)

---

## 🔌 Backend (FastAPI)

### Start the backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Available API Endpoints

| Method | Endpoint        | Description                 |
| ------ | --------------- | --------------------------- |
| POST   | `/            ` | Detect plates live from cam |
| POST   | `/detect/image` | Detect plates from an image |
| POST   | `/detect/video` | Detect plates from video    |

### Sample Image API Response

```json
{
  "detections": [
    {
      "id": 1,
      "plate_number": "MH20EE0943",
      "confidence": 0.85
    }
  ],
  "count": 1,
  "annotated_image": "<base64>"
}
```

---

## 🎨 Frontend

* Upload images/videos
* View original vs detected output
* Displays bounding boxes and OCR results

> Frontend consumes the FastAPI endpoints directly.

---

## 🗄️ Database

* Stores:

  * Plate number
  * Confidence score
  * Image path
  * Source (image/video)

Used for auditing, analytics, and future improvements.

---

## ⚠️ OCR Status

* OCR is currently **beta**
* Detection is stable
* OCR accuracy improves with:

  * Better crops
  * Fine-tuned OCR model
  * Indian plate-specific data

---

## 🧪 Future Improvements

* 🔠 OCR fine-tuning for Indian plates
* 🎥 Real-time video stream support
* 📊 Analytics dashboard
* 🧠 Plate tracking across frames
* 🔒 Authentication & access control

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repo
2. Create a new branch
3. Commit your changes
4. Open a pull request

---

## 📜 License

This project is for educational and research purposes.

---

## 🙌 Acknowledgements

* YOLO / Ultralytics
* OpenCV
* FastAPI
* PaddleOCR / OCR engines

---

**RoadEye-LPR** — making roads smarter 🚦
