"""
Mock sensor readings that simulate the ESP32 IoT node (PIR, distance,
vibration) until the real hardware arrives.

Once the ESP32 is wired up, replace the bodies of read_pir(), read_distance_cm(),
and read_vibration() with real serial/HTTP reads from the board. Nothing else
in the pipeline (fusion, dashboard, database) needs to change -- they only
depend on read_all() returning a dict with these three keys.
"""
import random
import time

# Simple state machine so the simulation isn't pure noise: motion "events"
# happen in short bursts, similar to a person actually walking through.
_last_event_time = 0.0
_event_active = False


def _maybe_trigger_event():
    global _last_event_time, _event_active
    now = time.time()
    if not _event_active and now - _last_event_time > 8:
        if random.random() < 0.15:  # ~15% chance to start a burst each check
            _event_active = True
            _last_event_time = now
    elif _event_active and now - _last_event_time > 4:
        _event_active = False
        _last_event_time = now
    return _event_active


def read_pir():
    """True if motion is 'detected' by the simulated PIR sensor."""
    return _maybe_trigger_event() or random.random() < 0.03


def read_distance_cm():
    """Simulated distance reading in cm. Lower = closer / more suspicious."""
    if _event_active:
        return round(random.uniform(80, 250), 1)
    return round(random.uniform(300, 600), 1)


def read_vibration():
    """Simulated vibration intensity, 0.0 to 1.0."""
    if _event_active:
        return round(random.uniform(0.4, 0.9), 2)
    return round(random.uniform(0.0, 0.15), 2)


def read_all():
    return {
        "pir": read_pir(),
        "distance_cm": read_distance_cm(),
        "vibration": read_vibration(),
    }
