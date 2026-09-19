# Cyber Mosquito — DSU Hackathon

Complete demo stack:

- `backend/` — FastAPI telemetry API + dashboard server
- `dashboard/` — browser dashboard with RF channel activity, rover telemetry, threat card, controls, event log
- `esp32/node1_rover/` — rover firmware: Wi-Fi scan, RSSI/channel telemetry, motor control, backend HTTP API
- `esp32/node2_simulation/` — controlled AP simulation node
- `camera/` — optional USB-camera MJPEG server
- `data/` — runtime data directory

## 1. Backend

Windows:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open:

`http://127.0.0.1:8000`

Find the PC's LAN IP with `ipconfig`. Example:

`http://192.168.1.20:8000`

The ESP32 must be able to reach that IP.

## 2. Node 1

Open `esp32/node1_rover/node1_rover.ino` in Arduino IDE.

Install/use:
- ESP32 Arduino core
- `HTTPClient`, `WiFi` are included with the ESP32 core

Set:

```cpp
WIFI_SSID
WIFI_PASSWORD
BACKEND_HOST
```

Example:

```cpp
const char* BACKEND_HOST = "192.168.1.20";
const int BACKEND_PORT = 8000;
```

Use GPIO 18/19 and 21/22 for the motor driver unless your hardware uses different safe GPIOs.

Start with the wheels off the ground.

## 3. Node 2

Upload `esp32/node2_simulation/node2_simulation.ino`.

Serial commands:

- `N` = normal AP
- `A` = controlled attack simulation AP
- `S` = status

## 4. Dashboard

The dashboard is served by FastAPI. It polls `/api/telemetry` and sends motor commands to `/api/rover/command`.

## 5. Camera

Camera support is optional. See `camera/README.md`.

This project only uses a controlled AP simulation for the security demonstration. It does not implement deauthentication, jamming, credential capture, or disruption of third-party networks.
