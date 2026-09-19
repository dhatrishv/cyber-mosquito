import os
import time
from collections import deque
from pathlib import Path

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "dashboard" / "index.html"

NODE1_COMMAND_URL = os.getenv(
    "NODE1_COMMAND_URL",
    ""
).rstrip("/")

app = FastAPI(title="Cyber Mosquito Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

latest = {
    "rover": {
        "online": False,
        "state": "OFFLINE",
        "direction": "STOPPED",
        "moving": False,
    },
    "rf": {
        "targetDetected": False,
        "targetSSID": "CYBER-TEST-ATTACK",
        "targetRSSI": -100,
        "targetChannel": -1,
        "networkCount": 0,
        "channels": [0] * 13,
        "threatType": "NONE",
    },
    "system": {
        "uptime": 0,
        "lastEvent": "Waiting for rover",
        "lastSeen": 0,
    },
}

events = deque(maxlen=100)


class Telemetry(BaseModel):
    rover: dict
    rf: dict
    system: dict


class Command(BaseModel):
    command: str


class Event(BaseModel):
    message: str
    level: str = "INFO"


def add_event(message: str, level: str = "INFO"):
    events.appendleft({
        "time": time.time(),
        "level": level,
        "message": message,
    })


@app.get("/")
def dashboard():
    return FileResponse(DASHBOARD)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/telemetry")
def get_telemetry():
    data = dict(latest)
    data["rover"] = dict(latest["rover"])
    data["rf"] = dict(latest["rf"])
    data["system"] = dict(latest["system"])

    age = time.time() - data["system"].get("lastSeen", 0)
    data["rover"]["online"] = age < 10

    if not data["rover"]["online"]:
        data["rover"]["state"] = "OFFLINE"

    return data


@app.post("/api/telemetry")
def post_telemetry(data: Telemetry):
    global latest

    old_target = latest["rf"].get("targetDetected", False)
    new_target = data.rf.get("targetDetected", False)

    latest = data.model_dump()
    latest["system"]["lastSeen"] = time.time()

    if new_target and not old_target:
        add_event(
            "Controlled attack simulation detected",
            "ALERT",
        )
    elif not new_target and old_target:
        add_event(
            "Controlled target no longer detected",
            "INFO",
        )

    return {"ok": True}


@app.get("/api/events")
def get_events():
    return list(events)


@app.post("/api/events")
def post_event(data: Event):
    add_event(data.message, data.level)
    return {"ok": True}


@app.post("/api/rover/command")
def rover_command(command: Command):
    allowed = {"F", "B", "L", "R", "S"}

    if command.command not in allowed:
        return {"ok": False, "error": "Invalid command"}

    # If Node 1 exposes an HTTP command endpoint, forward it.
    if NODE1_COMMAND_URL:
        try:
            response = requests.get(
                f"{NODE1_COMMAND_URL}/cmd",
                params={"c": command.command},
                timeout=2,
            )
            return {
                "ok": response.ok,
                "forwarded": True,
            }
        except requests.RequestException as exc:
            return {
                "ok": False,
                "forwarded": False,
                "error": str(exc),
            }

    # Backend-only demo mode.
    direction = {
        "F": "FORWARD",
        "B": "BACKWARD",
        "L": "LEFT",
        "R": "RIGHT",
        "S": "STOPPED",
    }[command.command]

    latest["rover"]["direction"] = direction
    latest["rover"]["moving"] = command.command != "S"
    latest["rover"]["state"] = (
        "MANUAL" if command.command != "S" else "STOPPED"
    )

    add_event(f"Rover command: {direction}", "INFO")

    return {"ok": True, "forwarded": False}
