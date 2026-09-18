# Cyber Mosquito

Cyber Mosquito is a software-first hackathon project for an ESP32-based 2WD robot used in **authorized and controlled RF anomaly investigation** demos.

## Architecture

ESP32-S3 (future)  
→ Wi-Fi / HTTP JSON  
→ Python Flask backend  
→ HTML/CSS/JavaScript dashboard

For now, a built-in simulator drives the full workflow without hardware.

## Project Structure

```
cyber-mosquito/
├── backend/
├── dashboard/
├── esp32/
├── camera/
├── data/
├── API_CONTRACT.md
└── README.md
```

## Quick Start

From repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/app.py
```

In another terminal (same repo root):

```bash
python3 -m http.server 8080
```

Then open:

- Dashboard: `http://127.0.0.1:8080/dashboard/`
- Backend API: `http://127.0.0.1:5000/api/status`

## Simulator Flow

The simulator continuously loops through:

BASELINE → SCAN → DETECT → MEASURE → MOVE → MAP → LOCALIZE → ALERT

It demonstrates:

- robot movement across a grid
- changing RSSI/signal values
- anomaly state transitions
- heatmap-style RF measurement points
- **Estimated Source Region** output
- event timeline updates

## API Endpoints

- `GET /api/status`
- `GET /api/rf`
- `GET /api/events`
- `GET /api/investigation`
- `POST /api/command`

See [`API_CONTRACT.md`](API_CONTRACT.md) for full request/response details and ESP32 integration contract.

## Testing Robot Commands

Example command:

```bash
curl -X POST http://127.0.0.1:5000/api/command \
  -H "Content-Type: application/json" \
  -d '{"command":"FORWARD","duration_ms":500}'
```

## Notes

- Dashboard values are API-driven (no hard-coded telemetry).
- If backend is unavailable, dashboard shows offline indicators.
- No database is used yet; baseline and observations are JSON files.
