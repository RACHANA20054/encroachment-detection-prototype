# Encroachment Detection — Software Prototype (No Hardware Required Yet)

This runs the full detection pipeline on your laptop's webcam, with the
ESP32 sensor readings (PIR, distance, vibration) **simulated** in
`sensors/mock_sensors.py`. It's meant to let you build, test, and demo the
software side while waiting for components to arrive.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

First run will auto-download the YOLOv8n model weights (~6MB).

## Run

```bash
python app.py
```

Then open **http://localhost:5000** in your browser. You should see:
- Live webcam feed (left panel)
- Same feed with detection boxes drawn (middle panel) — green box = normal,
  red box = ALERT status
- Live results panel (right) — fusion score, encroachment %, ESI severity,
  simulated sensor readings
- A table of recent logged events at the bottom

Walk in front of your webcam and stay inside the blue rectangle (the ROI —
your simulated "protected boundary") to trigger detections. The mock PIR/
distance/vibration sensors fire randomly in short bursts every so often —
that's expected, it's just standing in for real hardware.

## What to test right now

- Does YOLOv8 reliably detect a person at your webcam's typical distance/lighting?
- Does the ROI rectangle in `app.py` (the `ROI = (...)` line) need adjusting
  for your camera's resolution/framing?
- Do the fusion score and ESI values feel reasonable, or do the weights in
  `fusion/fusion_engine.py` need tuning?
- Does the dashboard layout/wording match what you want for the final demo?

## When the ESP32 arrives

Only **`sensors/mock_sensors.py`** needs to change — replace the three
`read_*()` function bodies with real serial or HTTP reads from the ESP32.
Everything else (detection, fusion, database, dashboard) stays the same.

## When you move to Raspberry Pi

In `app.py`, change `cv2.VideoCapture(0)` (both places) to your Pi Camera
source. Nothing else changes.

## Known limitations (be upfront about these in your report/viva)

- The ROI is a simple rectangle, not a calibrated real-world boundary —
  this is a prototype/image-space ROI, not real-world land area (see the
  project report's note on this distinction).
- Fusion weights and ESI thresholds are starting values from the proposal,
  not yet validated against labelled test data.
- Mock sensor data is randomized in bursts to *simulate* activity — it is
  not connected to anything physical yet.
