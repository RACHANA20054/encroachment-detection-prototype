# Encroachment Detection — Software + ESP32 Hardware

## Software setup (works today, no hardware required)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000**. Uses simulated sensor data by default
(`sensors/mock_sensors.py`) so you can test everything before hardware
arrives.

## Switching to your real ESP32

1. **Flash the firmware**: open `esp32_firmware/sensor_node.ino` in the
   Arduino IDE. Fill in your Wi-Fi SSID/password near the top of the file.
   Install the ESP32 board package if you haven't (see comment at top of
   the file for the exact steps). Select your board under
   `Tools > Board`, then upload.

2. **Get the ESP32's IP address**: open the Arduino IDE's Serial Monitor
   (115200 baud) right after uploading. Once it connects to Wi-Fi, it
   prints its IP address, e.g. `192.168.1.50`.

3. **Test it standalone first**: open `http://<that IP>/sensors` in a
   browser. You should see JSON like:
   ```json
   {"pir": false, "distance_cm": 182.4, "vibration": 0.0}
   ```
   Wave your hand in front of the PIR sensor and refresh — `pir` should
   flip to `true`. If this doesn't work, fix it here before touching the
   Python side — it isolates hardware problems from software problems.

4. **Point the Python side at it**: open `sensors/esp32_sensors.py` and
   set `ESP32_IP` to the address from step 2.

5. **Swap the import in `app.py`**: change
   ```python
   from sensors.mock_sensors import read_all
   ```
   to
   ```python
   from sensors.esp32_sensors import read_all
   ```

6. Run `python app.py` again as usual. Everything else — detection,
   fusion, database, dashboard — is completely unchanged.

## Wiring reference

| Sensor | ESP32 Pin | Notes |
|---|---|---|
| PIR (HC-SR501) OUT | GPIO 27 | Digital input |
| Ultrasonic (HC-SR04) TRIG | GPIO 5 | Digital output |
| Ultrasonic (HC-SR04) ECHO | GPIO 18 | **Needs a voltage divider** (5V→3.3V) |
| Vibration (SW-420) OUT | GPIO 26 | Digital input |
| Buzzer + | GPIO 4 | Digital output |
| LED + (through resistor) | GPIO 15 | Digital output |
| All GND | ESP32 GND | Common ground for every sensor |

⚠️ HC-SR04's ECHO pin outputs 5V, but ESP32 GPIO is only 3.3V-tolerant.
Use a simple resistor voltage divider (e.g. 1kΩ + 2kΩ) between ECHO, GND,
and the ESP32 pin — search "HC-SR04 ESP32 voltage divider" for the
standard, well-documented circuit if you're unsure.

## Testing the camera in isolation

```bash
python test_camera.py
```
No Flask, no YOLO — just confirms your webcam and OpenCV setup work.

## Known limitations (be upfront about these in your report/viva)

- ROI is a simple rectangle, not a calibrated real-world boundary.
- Fusion weights and ESI thresholds are starting values, not yet
  validated against labelled test data — expect to tune them once you
  have real sensor readings alongside real detections.
- `esp32_sensors.py` falls back to the last known good reading if the
  ESP32 is briefly unreachable, rather than crashing — good for demo
  reliability, but worth mentioning as a design decision if asked.
