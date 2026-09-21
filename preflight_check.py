"""
Pre-presentation safety check.
Run this BEFORE your demo to catch problems early.
Does not modify anything — read-only checks.
"""
import subprocess
import sys
import os

def ok(msg):
    print(f"  [OK]   {msg}")

def fail(msg):
    print(f"  [FAIL] {msg}")

def warn(msg):
    print(f"  [WARN] {msg}")

print("=" * 55)
print("PRE-PRESENTATION SAFETY CHECK")
print("=" * 55)

# 1. Check we're in the right directory
print("\n[1] Project directory")
required_files = ["app.py", "detection/yolo_detector.py", "templates/index.html"]
missing = [f for f in required_files if not os.path.exists(f)]
if missing:
    fail(f"Missing files: {missing}. Are you in the right folder?")
else:
    ok("All required files found.")

# 2. Check model file exists
print("\n[2] Trained model")
model_path = "runs/detect/runs/detect/encroachment_clean_v3/weights/best.pt"
if os.path.exists(model_path):
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    ok(f"Model found ({size_mb:.1f} MB) at {model_path}")
else:
    fail(f"Model NOT found at {model_path} — detection will fail!")

# 3. Check port 5001 status
print("\n[3] Port 5001")
try:
    result = subprocess.run(["lsof", "-i", ":5001"], capture_output=True, text=True, timeout=5)
    if result.stdout.strip():
        warn("Port 5001 is currently IN USE. If you're about to start app.py fresh,")
        warn("you may need to kill the existing process first:")
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) > 1:
                warn(f"   kill -9 {parts[1]}")
    else:
        ok("Port 5001 is free.")
except Exception as e:
    warn(f"Could not check port status: {e}")

# 4. Check camera index 1 opens
print("\n[4] Camera (index 1 — S25/DroidCam/OBS)")
try:
    import cv2
    cap = cv2.VideoCapture(1)
    opened = cap.isOpened()
    if opened:
        ret, frame = cap.read()
        if ret and frame is not None:
            brightness = frame.mean()
            ok(f"Camera opened. Frame shape: {frame.shape}, avg brightness: {brightness:.1f}")
            if brightness < 15:
                warn("Frame is very dark — check OBS/DroidCam connection and lighting.")
        else:
            fail("Camera opened but no frame could be read.")
    else:
        fail("Could not open camera at index 1. Check OBS Virtual Camera is running.")
    cap.release()
except Exception as e:
    fail(f"Camera check crashed: {e}")

# 5. Check model loads and has correct classes
print("\n[5] Model classes")
try:
    from ultralytics import YOLO
    m = YOLO(model_path)
    expected = {0: 'cement_bag', 1: 'brick', 2: 'cement_block', 3: 'foundation_block', 4: 'owner', 5: 'encroacher'}
    if m.names == expected:
        ok(f"Model has correct 6 classes: {list(expected.values())}")
    else:
        fail(f"Model classes don't match expected! Got: {m.names}")
except Exception as e:
    fail(f"Could not load model: {e}")

# 6. Check git status (uncommitted changes warning)
print("\n[6] Git status")
try:
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5)
    if result.stdout.strip():
        warn("You have uncommitted changes. Not a problem for the demo, just noting:")
        for line in result.stdout.strip().split("\n")[:5]:
            warn(f"   {line}")
    else:
        ok("Working tree clean, everything committed.")
except Exception as e:
    warn(f"Could not check git status: {e}")

print("\n" + "=" * 55)
print("CHECK COMPLETE — review any [FAIL] or [WARN] lines above")
print("=" * 55)
