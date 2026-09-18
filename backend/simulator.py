"""Core simulator for end-to-end Cyber Mosquito dashboard demos."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from detector import BaselineDetector
from localization import estimate_source_region
from robot import RobotState
from rf import RFReading


def _iso(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts or time.time(), tz=timezone.utc).isoformat()


class CyberMosquitoSimulator:
    PIPELINE = ["BASELINE", "SCAN", "DETECT", "MEASURE", "MOVE", "MAP", "LOCALIZE", "ALERT"]
    PHASE_SECONDS = 3

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self._baseline_path = root / "data" / "baseline.json"
        self._observations_path = root / "data" / "observations.json"

        self.detector = BaselineDetector(self._baseline_path)
        self.robot = RobotState()
        self.rf = RFReading()

        self.route = [
            {"x": 0, "y": 0},
            {"x": 1, "y": 0},
            {"x": 2, "y": 0},
            {"x": 2, "y": 1},
            {"x": 2, "y": 2},
            {"x": 3, "y": 2},
            {"x": 3, "y": 3},
        ]
        self.signal_profile = [-75, -70, -65, -59, -53, -48, -43]
        self.phase_messages = [
            "System initialized",
            "RF monitoring active",
            "Baseline established",
            "Unexpected RF activity detected",
            "Anomaly detected",
            "Robot dispatched",
            "Signal measurement collected",
            "Investigation in progress",
            "Estimated source region identified",
            "Investigation complete",
        ]

        self.start_ts = time.time()
        self.manual_movement = "STOP"
        self.manual_until = 0.0
        self.lock = threading.Lock()

    def _phase_index(self) -> int:
        elapsed = int(time.time() - self.start_ts)
        return (elapsed // self.PHASE_SECONDS) % 12

    def _move_index(self, phase_index: int) -> int:
        if phase_index < 5:
            return 0
        return min(phase_index - 5, len(self.route) - 1)

    def _activity_from_signal(self, signal_dbm: int) -> str:
        if signal_dbm <= -65:
            return "LOW"
        if signal_dbm <= -53:
            return "MEDIUM"
        return "HIGH"

    def _movement_from_step(self, previous: Dict[str, int], current: Dict[str, int]) -> str:
        dx = current["x"] - previous["x"]
        dy = current["y"] - previous["y"]
        if dx > 0:
            return "RIGHT"
        if dx < 0:
            return "LEFT"
        if dy > 0:
            return "FORWARD"
        if dy < 0:
            return "BACKWARD"
        return "STOP"

    def _apply_manual_command(self, command: str, duration_ms: int) -> None:
        now = time.time()
        self.manual_movement = command
        self.manual_until = now + max(duration_ms, 0) / 1000
        self.phase_messages.append(f"Manual command executed: {command}")

        if command == "FORWARD":
            self.robot.y = min(self.robot.y + 1, 6)
        elif command == "BACKWARD":
            self.robot.y = max(self.robot.y - 1, 0)
        elif command == "LEFT":
            self.robot.x = max(self.robot.x - 1, 0)
        elif command == "RIGHT":
            self.robot.x = min(self.robot.x + 1, 6)

    def command(self, command: str, duration_ms: int) -> Dict[str, object]:
        allowed = {"FORWARD", "BACKWARD", "LEFT", "RIGHT", "STOP"}
        if command not in allowed:
            return {"accepted": False, "error": f"Unsupported command: {command}"}

        with self.lock:
            self._apply_manual_command(command, duration_ms)
            return {
                "accepted": True,
                "command": command,
                "duration_ms": duration_ms,
                "timestamp": _iso(),
            }

    def _current_cycle_state(self) -> Dict[str, object]:
        phase_idx = self._phase_index()
        move_idx = self._move_index(phase_idx)

        point = self.route[move_idx]
        signal_dbm = self.signal_profile[move_idx]
        frequency = 2437 if phase_idx < 3 else 2462
        detector_result = self.detector.classify(frequency, signal_dbm)

        mode = "IDLE"
        pipeline_stage = "BASELINE"
        if phase_idx >= 1:
            mode = "SCANNING"
            pipeline_stage = "SCAN"
        if phase_idx >= 3:
            mode = "INVESTIGATING"
            pipeline_stage = "DETECT"
        if phase_idx >= 4:
            pipeline_stage = "MEASURE"
        if phase_idx >= 5:
            pipeline_stage = "MOVE"
        if phase_idx >= 6:
            pipeline_stage = "MAP"
        if phase_idx >= 8:
            pipeline_stage = "LOCALIZE"
        if phase_idx >= 10:
            pipeline_stage = "ALERT"

        measurement_points = [
            {"x": self.route[i]["x"], "y": self.route[i]["y"], "signal_dbm": self.signal_profile[i]}
            for i in range(move_idx + 1)
        ]
        source_estimate = estimate_source_region(measurement_points)

        now = time.time()
        if now <= self.manual_until:
            movement = self.manual_movement
        else:
            previous_point = self.route[max(move_idx - 1, 0)]
            movement = self._movement_from_step(previous_point, point)

        self.robot.mode = mode
        self.robot.movement = movement
        self.robot.x = point["x"]
        self.robot.y = point["y"]
        self.robot.battery = max(20, 92 - move_idx * 4)
        self.robot.distance_cm = max(18, 50 - move_idx * 4)
        self.robot.rssi = -48 + move_idx * 2

        self.rf.frequency_mhz = frequency
        self.rf.signal_dbm = signal_dbm
        self.rf.activity = self._activity_from_signal(signal_dbm)
        self.rf.status = "ANOMALY" if not detector_result["expected"] else "NORMAL"

        event_messages = self.phase_messages[: min(phase_idx + 1, len(self.phase_messages))]
        events = [
            {
                "id": index + 1,
                "message": message,
                "timestamp": _iso(self.start_ts + index * self.PHASE_SECONDS),
            }
            for index, message in enumerate(event_messages)
        ]

        anomaly = {
            "title": "RF Anomaly",
            "description": detector_result["label"],
            "frequency_mhz": frequency,
            "signal_dbm": signal_dbm,
            "first_seen": events[3]["timestamp"] if len(events) > 3 else _iso(self.start_ts),
            "investigation_status": (
                "Estimated Source Region identified" if phase_idx >= 8 else "Investigation in progress"
            ),
        }

        investigation = {
            "stage": pipeline_stage,
            "pipeline": self.PIPELINE,
            "anomaly_detected": not detector_result["expected"],
            "anomaly": anomaly,
            "measurements": measurement_points,
            "estimated_source_region": source_estimate,
            "completed": phase_idx >= 11,
            "timestamp": _iso(),
        }

        status = {
            "robot_id": self.robot.robot_id,
            "status": self.robot.status,
            "mode": self.robot.mode,
            "movement": self.robot.movement,
            "battery": self.robot.battery,
            "distance_cm": self.robot.distance_cm,
            "rssi": self.robot.rssi,
            "position": {
                "x": self.robot.x,
                "y": self.robot.y,
                "zone": self.robot.zone,
            },
            "timestamp": _iso(),
        }

        rf = {
            "frequency_mhz": self.rf.frequency_mhz,
            "signal_dbm": self.rf.signal_dbm,
            "activity": self.rf.activity,
            "status": self.rf.status,
            "timestamp": _iso(),
        }

        self._observations_path.parent.mkdir(parents=True, exist_ok=True)
        with self._observations_path.open("w", encoding="utf-8") as handle:
            json.dump(measurement_points, handle, indent=2)

        return {
            "status": status,
            "rf": rf,
            "events": events,
            "investigation": investigation,
        }

    def snapshot(self) -> Dict[str, object]:
        with self.lock:
            return self._current_cycle_state()
