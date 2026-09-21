"""
Runs the custom V3 YOLO model (cement_bag, brick, cement_block,
foundation_block, owner, encroacher) on a video frame and checks
whether detections fall inside the ROI.
"""
from ultralytics import YOLO

MODEL_PATH = "runs/detect/runs/detect/encroachment_clean_v3/weights/best.pt"

CLASS_NAMES = {
    0: "cement_bag",
    1: "brick",
    2: "cement_block",
    3: "foundation_block",
    4: "owner",
    5: "encroacher",
}

CONF_THRESHOLDS = {
    0: 0.30,
    1: 0.30,
    2: 0.30,
    3: 0.30,
    4: 0.35,
    5: 0.35,
}

MIN_CONF = min(CONF_THRESHOLDS.values())

_model = None


def get_model():
    global _model
    if _model is None:
        _model = YOLO(MODEL_PATH)
    return _model


def _box_area(box):
    x1, y1, x2, y2 = box
    return max(0, x2 - x1) * max(0, y2 - y1)


def _iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = _box_area(box1) + _box_area(box2) - inter
    return inter / union if union > 0 else 0


def detect_objects(frame):
    model = get_model()
    results = model(frame, conf=MIN_CONF, iou=0.45, verbose=False)

    candidates = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            if cls_id not in CLASS_NAMES:
                continue
            if conf < CONF_THRESHOLDS[cls_id]:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            candidates.append({
                "label": CLASS_NAMES[cls_id],
                "confidence": round(conf, 3),
                "box": [round(x1), round(y1), round(x2), round(y2)],
            })

    # Cross-class suppression: keep only the highest-confidence label
    # per overlapping region (stops e.g. a brick also being labeled
    # a weak "owner"/"encroacher" guess at the same time).
    candidates.sort(key=lambda c: c["confidence"], reverse=True)
    kept = []
    for c in candidates:
        if not any(_iou(c["box"], k["box"]) > 0.3 for k in kept):
            kept.append(c)
    return kept


def box_in_roi(box, roi):
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
