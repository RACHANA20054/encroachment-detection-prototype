"""
Real sensor readings from the physical ESP32 node, fetched over Wi-Fi.

This is a drop-in replacement for sensors/mock_sensors.py -- it exposes the
exact same read_all() function returning the exact same dict shape, so
nothing else in the pipeline (fusion, dashboard, database) needs to change.

SETUP:
1. Flash esp32_firmware/sensor_node.ino to your ESP32 (fill in your Wi-Fi
   credentials in that file first).
2. Open the Arduino IDE Serial Monitor after upload -- it will print the
   ESP32's IP address once connected to Wi-Fi. Copy that IP.
3. Paste it into ESP32_IP below.
4. In app.py, change:
       from sensors.mock_sensors import read_all
   to:
       from sensors.esp32_sensors import read_all
"""
import requests

ESP32_IP = "192.168.43.99"  # <-- replace with your ESP32's actual IP address
SENSOR_URL = f"http://{ESP32_IP}/sensors"
ALERT_URL = f"http://{ESP32_IP}/alert"
TIMEOUT_SECONDS = 1.0

_last_good_reading = {"pir": False, "distance_cm": None, "vibration": 0.0}
_last_source = "none"   # tracks whether last call succeeded


def read_all():
    """
    Fetches live sensor readings from the ESP32.

    Returns a dict with keys:
        pir, distance_cm, vibration  -- sensor values
        source  -- "live"   : freshly fetched from the real ESP32
                   "cached" : ESP32 was unreachable; last known value returned
    """
    global _last_good_reading, _last_source
    try:
        response = requests.get(SENSOR_URL, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        _last_good_reading = {
            "pir": bool(data.get("pir", False)),
            "distance_cm": data.get("distance_cm"),
            "vibration": float(data.get("vibration", 0.0)),
        }
        _last_source = "live"
        print(f"[esp32_sensors] OK  — live data: {_last_good_reading}")
    except (requests.RequestException, ValueError) as e:
        _last_source = "cached"
        print(f"[esp32_sensors] FAIL — cannot reach ESP32 ({e}); returning cached values")

    return {**_last_good_reading, "source": _last_source}


def trigger_local_alert():
    """Optional: tells the ESP32 to sound its buzzer/LED directly."""
    try:
        requests.post(ALERT_URL, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as e:
        print(f"[esp32_sensors] Could not trigger ESP32 alert: {e}")
