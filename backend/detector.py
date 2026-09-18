"""Baseline detector for simulated RF observations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class BaselineDetector:
    """Compares observations against known baseline values."""

    def __init__(self, baseline_file: str | Path) -> None:
        self.baseline_file = Path(baseline_file)
        self.baseline = self._load_baseline()

    def _load_baseline(self) -> Dict[str, Any]:
        if not self.baseline_file.exists():
            return {"known_frequencies_mhz": [2412, 2437, 2462], "max_expected_signal_dbm": -50}

        with self.baseline_file.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def classify(self, frequency_mhz: int, signal_dbm: int) -> Dict[str, Any]:
        known_frequencies = set(self.baseline.get("known_frequencies_mhz", []))
        max_expected_signal = int(self.baseline.get("max_expected_signal_dbm", -50))

        expected = frequency_mhz in known_frequencies and signal_dbm <= max_expected_signal
        status = "EXPECTED" if expected else "UNEXPECTED"
        label = "Known/Expected Activity" if expected else "Unexpected RF Activity"

        return {
            "status": status,
            "label": label,
            "expected": expected,
            "frequency_mhz": frequency_mhz,
            "signal_dbm": signal_dbm,
        }
