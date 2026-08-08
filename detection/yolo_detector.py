"""
Runs YOLOv8 on a video frame and checks whether detections fall inside the
Region of Interest (ROI) representing the protected boundary.

Works on a laptop webcam today. Swap the camera source for the Pi Camera
later (in app.py) without changing anything in this file.
"""
from ultralytics import YOLO

MODEL_PATH = "yolov8n.pt"  # auto-downloads on first run
RELEVANT_CLASSES = {"person", "car", "truck", "motorcycle", "bicycle"}
CONFIDENCE_THRESHOLD = 0.4

_model = None


def get_model():
    global _model
    if _model is None:
        _model = YOLO(MODEL_PATH)
    return _model


def detect_objects(frame):
    model = get_model()
    results = model(frame, verbose=False)
    detections = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])
            if label in RELEVANT_CLASSES and conf >= CONFIDENCE_THRESHOLD:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "label": label,
                    "confidence": round(conf, 3),
                    "box": [round(x1), round(y1), round(x2), round(y2)],
                })
    return detections


def box_in_roi(box, roi):
    """Checks if a detection box overlaps the ROI rectangle."""
    bx1, by1, bx2, by2 = box
    rx1, ry1, rx2, ry2 = roi
    ox1, oy1 = max(bx1, rx1), max(by1, ry1)
    ox2, oy2 = min(bx2, rx2), min(by2, ry2)
    if ox2 <= ox1 or oy2 <= oy1:
        return False, 0.0
    overlap_area = (ox2 - ox1) * (oy2 - oy1)
    box_area = max((bx2 - bx1) * (by2 - by1), 1)
    return True, overlap_area / box_area


def encroachment_percentage(detections, roi):
    """Estimated % of the ROI area covered by relevant detected objects."""
    rx1, ry1, rx2, ry2 = roi
    roi_area = max((rx2 - rx1) * (ry2 - ry1), 1)
    covered = 0
    for d in detections:
        in_roi, _ = box_in_roi(d["box"], roi)
        if in_roi:
            bx1, by1, bx2, by2 = d["box"]
            ox1, oy1 = max(bx1, rx1), max(by1, ry1)
            ox2, oy2 = min(bx2, rx2), min(by2, ry2)
            covered += max(0, ox2 - ox1) * max(0, oy2 - oy1)
    return round(min(covered / roi_area, 1.0) * 100, 2)
