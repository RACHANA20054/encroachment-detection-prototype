"""
Mock sensor readings that simulate the ESP32 IoT node (PIR, distance,
vibration) until the real hardware arrives.

Once the ESP32 is wired up, use sensors/esp32_sensors.py instead (same
read_all() interface, real data). Nothing else in the pipeline (fusion,
dashboard, database) needs to change.
"""
import random
import time

_last_event_time = 0.0
_event_active = False


def _maybe_trigger_event():
    global _last_event_time, _event_active
    now = time.time()
    if not _event_active and now - _last_event_time > 8:
        if random.random() < 0.15:
            _event_active = True
            _last_event_time = now
    elif _event_active and now - _last_event_time > 4:
        _event_active = False
        _last_event_time = now
    return _event_active


def read_pir():
    return _maybe_trigger_event() or random.random() < 0.03


def read_distance_cm():
    if _event_active:
        return round(random.uniform(80, 250), 1)
    return round(random.uniform(300, 600), 1)


def read_vibration():
    if _event_active:
        return round(random.uniform(0.4, 0.9), 2)
    return round(random.uniform(0.0, 0.15), 2)


def read_all():
    return {
        "pir": read_pir(),
        "distance_cm": read_distance_cm(),
        "vibration": read_vibration(),
    }
