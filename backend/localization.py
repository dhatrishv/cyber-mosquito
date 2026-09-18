"""Demo RF localization helper.

This model provides an estimated source region for visualization only.
Indoor RF localization is approximate and affected by reflections,
walls, interference, and antenna orientation.
"""

from __future__ import annotations

from typing import Dict, List


def _zone_from_xy(x: int, y: int) -> str:
    return f"{chr(ord('A') + max(min(y, 25), 0))}{max(x, 0) + 1}"


def estimate_source_region(measurements: List[Dict[str, int]]) -> Dict[str, object]:
    if not measurements:
        return {
            "x": 0,
            "y": 0,
            "zone": "A1",
            "label": "Estimated Source Region",
            "confidence": "LOW",
            "notes": "Insufficient data for estimate.",
        }

    weights = [max(reading["signal_dbm"] + 100, 1) for reading in measurements]
    total_weight = sum(weights)

    x = round(sum(point["x"] * weight for point, weight in zip(measurements, weights)) / total_weight)
    y = round(sum(point["y"] * weight for point, weight in zip(measurements, weights)) / total_weight)

    strongest = max(measurements, key=lambda item: item["signal_dbm"])
    confidence = "MEDIUM" if len(measurements) < 5 else "HIGH"

    return {
        "x": x,
        "y": y,
        "zone": _zone_from_xy(x, y),
        "label": "Estimated Source Region",
        "confidence": confidence,
        "strongest_point": strongest,
        "notes": (
            "Visualization estimate only. Indoor RF environments are noisy and"
            " multipath effects reduce precision."
        ),
    }
