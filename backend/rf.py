"""RF reading model for Cyber Mosquito simulator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RFReading:
    frequency_mhz: int = 2437
    signal_dbm: int = -61
    activity: str = "MEDIUM"
    status: str = "NORMAL"
