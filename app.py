"""
Runs the full prototype pipeline on your laptop webcam with simulated IoT
sensor data -- no ESP32 or Raspberry Pi required yet.

Run:
    pip install -r requirements.txt
    python app.py

Then open http://localhost:5000 in your browser.

Once the ESP32 arrives: replace sensors/mock_sensors.py's internals with real
reads, and swap cv2.VideoCapture(0) for your Pi Camera source when you move
to the Raspberry Pi. Nothing else needs to change.
"""
import cv2
import time
import threading
from flask import Flask, Response, jsonify, render_template

from detection.yolo_detector import detect_objects, box_in_roi, encroachment_percentage
from fusion.fusion_engine import fuse, severity_index
from sensors.mock_sensors import read_all
from database.db import init_db, log_event, get_recent_events

app = Flask(__name__)
init_db()

# ROI: rectangle in pixel coordinates -- adjust to your webcam resolution
# and where your "protected boundary" sits in frame.
ROI = (150, 80, 500, 400)  # x1, y1, x2, y2


class CameraStream:
    """
    Opens the webcam ONCE and shares frames with anyone who needs them,
    instead of every part of the app opening its own cv2.VideoCapture(0).
    Multiple simultaneous captures is what was causing the camera to stay
    busy/on unexpectedly.
    """
    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(
                "Could not open webcam. Close any other app using the camera "
                "(Zoom, Teams, another instance of this script, etc.) and try again."
            )
        self.lock = threading.Lock()
        self.frame = None
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            ok, frame = self.cap.read()
            if ok:
                with self.lock:
                    self.frame = frame
            else:
                time.sleep(0.1)

    def read(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def release(self):
        self.running = False
        time.sleep(0.2)
        self.cap.release()


camera = CameraStream(0)

latest_state = {
    "detections": [],
    "sensor_data": {},
    "fusion": {},
    "affected_percent": 0.0,
    "esi": {"esi": 0.0, "level": "Low"},
    "zone": "Zone-A",
}
_lock = threading.Lock()
_present_since = None


def object_risk_score(detections):
    if any(d["label"] == "person" for d in detections):
        return 0.9
    if any(d["label"] in ("car", "truck", "motorcycle") for d in detections):
        return 0.7
    return 0.3 if detections else 0.0


def process_loop():
    global _present_since
    last_log_time = 0

    while True:
        frame = camera.read()
        if frame is None:
            time.sleep(0.2)
            continue

        detections = detect_objects(frame)
        sensor_data = read_all()

        roi_hit = any(box_in_roi(d["box"], ROI)[0] for d in detections)
        if roi_hit:
            _present_since = _present_since or time.time()
        else:
            _present_since = None
        time_present = (time.time() - _present_since) if _present_since else 0

        fusion_result = fuse(detections, sensor_data, roi_hit, time_present)
        affected_pct = encroachment_percentage(detections, ROI) if detections else 0.0

        esi = severity_index(
            affected_percent=affected_pct,
            object_risk=object_risk_score(detections),
            duration_s=time_present,
            boundary_penetration=1.0 if roi_hit else 0.3,
            confidence=fusion_result["fusion_score"] / 100.0,
        )

        with _lock:
            latest_state.update({
                "detections": detections,
                "sensor_data": sensor_data,
                "fusion": fusion_result,
                "affected_percent": affected_pct,
                "esi": esi,
            })

        if fusion_result["status"] == "ALERT" and time.time() - last_log_time > 5:
            last_log_time = time.time()
            main_label = detections[0]["label"] if detections else "unknown"
            main_conf = detections[0]["confidence"] if detections else 0.0
            log_event(main_label, main_conf, fusion_result["fusion_score"],
                      affected_pct, esi["esi"], esi["level"])

        time.sleep(0.05)


def gen_frames(draw_detections=False):
    while True:
        frame = camera.read()
        if frame is None:
            time.sleep(0.1)
            continue
        frame = frame.copy()
        cv2.rectangle(frame, (ROI[0], ROI[1]), (ROI[2], ROI[3]), (255, 200, 0), 2)
        if draw_detections:
            with _lock:
                dets = list(latest_state["detections"])
                status = latest_state["fusion"].get("status")
            for d in dets:
                x1, y1, x2, y2 = d["box"]
                color = (0, 0, 255) if status == "ALERT" else (0, 200, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{d['label']} {d['confidence']:.2f}", (x1, max(y1 - 8, 12)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            continue
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
        time.sleep(0.03)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(False), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/video_feed_detected")
def video_feed_detected():
    return Response(gen_frames(True), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/status")
def api_status():
    with _lock:
        return jsonify(latest_state)


@app.route("/api/events")
def api_events():
    return jsonify(get_recent_events())


if __name__ == "__main__":
    t = threading.Thread(target=process_loop, daemon=True)
    t.start()
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    finally:
        camera.release()
        print("Camera released. Goodbye.")
