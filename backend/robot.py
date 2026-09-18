"""Robot state model for Cyber Mosquito simulator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RobotState:
    robot_id: str = "CM-01"
    status: str = "ONLINE"
    mode: str = "IDLE"
    movement: str = "STOP"
    battery: int = 87
    distance_cm: int = 42
    rssi: int = -52
    x: int = 0
    y: int = 0

    @property
    def zone(self) -> str:
        return f"{chr(ord('A') + max(self.y, 0))}{self.x + 1}"
