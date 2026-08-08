"""
Standalone webcam test -- no Flask, no YOLO, nothing else involved.

Run this FIRST if you're unsure whether your camera itself is working
before troubleshooting the full app.

Run:
    python test_camera.py

A window should pop up showing your live camera feed. Press 'q' to quit.
If this doesn't work, the problem is your camera/OpenCV setup, not the
Flask app or YOLO.
"""
import cv2

def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Could not open camera. Things to check:")
        print("  1. Is another app (Zoom, Teams, Camera app) using the camera right now?")
        print("  2. Does Windows have camera permission enabled for apps? "
              "(Settings > Privacy > Camera)")
        print("  3. Try changing cv2.VideoCapture(0) to cv2.VideoCapture(1) "
              "if you have multiple cameras")
        return

    print("Camera opened successfully. Press 'q' in the video window to quit.")
    frame_count = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            print("WARNING: Failed to read a frame from the camera.")
            break

        frame_count += 1
        cv2.putText(frame, f"Frame {frame_count} - press 'q' to quit",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Camera Test", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Camera released cleanly after {frame_count} frames. Test complete.")

if __name__ == "__main__":
    main()
