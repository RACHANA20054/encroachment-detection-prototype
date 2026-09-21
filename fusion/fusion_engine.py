"""
Sensor Fusion Engine + Encroachment Severity Index (ESI).

NOTE: weights and thresholds are starting points from the project proposal,
not scientifically validated -- tune against your own labelled test data.
"""

WEIGHTS = {
    "camera": 0.40,
    "pir": 0.20,
    "distance": 0.15,
    "vibration": 0.10,
    "roi_crossing": 0.10,
    "time_present": 0.05,
}

ALERT_THRESHOLD = 75
SUSPICIOUS_THRESHOLD = 40


def _normalize_distance(distance_cm, near=100, far=500):
    if distance_cm is None:
        return 0.0
    d = max(near, min(distance_cm, far))
    return round(1 - (d - near) / (far - near), 3)


def fuse(detections, sensor_data, roi_hit, time_present_s=0):
    camera_score = 1.0 if detections else 0.0
    pir_score = 1.0 if sensor_data.get("pir") else 0.0
    distance_score = _normalize_distance(sensor_data.get("distance_cm"))
    vibration_score = min(sensor_data.get("vibration", 0.0), 1.0)
    roi_score = 1.0 if roi_hit else 0.0
    time_score = min(time_present_s / 10.0, 1.0)

    score = (
        WEIGHTS["camera"] * camera_score
        + WEIGHTS["pir"] * pir_score
        + WEIGHTS["distance"] * distance_score
        + WEIGHTS["vibration"] * vibration_score
        + WEIGHTS["roi_crossing"] * roi_score
        + WEIGHTS["time_present"] * time_score
    ) * 100

    if score >= ALERT_THRESHOLD:
        status = "ALERT"
    elif score >= SUSPICIOUS_THRESHOLD:
        status = "SUSPICIOUS"
    else:
        status = "LOW"

    return {
        "fusion_score": round(score, 2),
        "status": status,
        "components": {
            "camera": camera_score,
            "pir": pir_score,
            "distance": distance_score,
            "vibration": vibration_score,
            "roi_crossing": roi_score,
            "time_present": time_score,
        },
    }


def severity_index(affected_percent, object_risk, duration_s, boundary_penetration, confidence):
    area_norm = min(affected_percent / 100.0, 1.0)
    duration_norm = min(duration_s / 30.0, 1.0)

    esi = (
        0.30 * area_norm
        + 0.25 * object_risk
        + 0.20 * duration_norm
        + 0.15 * boundary_penetration
        + 0.10 * confidence
    ) * 100

    if esi <= 30:
        level = "Low"
    elif esi <= 60:
        level = "Moderate"
    elif esi <= 80:
        level = "High"
    else:
        level = "Critical"

    return {"esi": round(esi, 2), "level": level}
