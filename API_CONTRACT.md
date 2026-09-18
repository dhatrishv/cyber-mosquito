# Cyber Mosquito API Contract

The dashboard communicates only with the Python backend over HTTP/JSON.

## Base URL

`http://127.0.0.1:5000`

## Endpoints

### GET /api/status
Returns current robot telemetry.

```json
{
  "robot_id": "CM-01",
  "status": "ONLINE",
  "mode": "IDLE",
  "movement": "STOP",
  "battery": 87,
  "distance_cm": 42,
  "rssi": -52,
  "position": {
    "x": 1,
    "y": 2,
    "zone": "B2"
  },
  "timestamp": "2026-09-18T04:00:00+00:00"
}
```

Units: `battery` = %, `distance_cm` = centimeters, `rssi` = dBm.

### GET /api/rf
Returns current RF state.

```json
{
  "frequency_mhz": 2437,
  "signal_dbm": -61,
  "activity": "MEDIUM",
  "status": "NORMAL",
  "timestamp": "2026-09-18T04:00:00+00:00"
}
```

Units: `frequency_mhz` = MHz, `signal_dbm` = dBm.

### GET /api/events
Returns timeline events.

```json
[
  {
    "id": 1,
    "message": "System initialized",
    "timestamp": "2026-09-18T04:00:00+00:00"
  }
]
```

### GET /api/investigation
Returns current stage, anomaly, measurements, and source estimate.

```json
{
  "stage": "MAP",
  "pipeline": ["BASELINE", "SCAN", "DETECT", "MEASURE", "MOVE", "MAP", "LOCALIZE", "ALERT"],
  "anomaly_detected": true,
  "anomaly": {
    "title": "RF Anomaly",
    "description": "Unexpected RF Activity",
    "frequency_mhz": 2462,
    "signal_dbm": -53,
    "first_seen": "2026-09-18T04:00:09+00:00",
    "investigation_status": "Investigation in progress"
  },
  "measurements": [
    { "x": 2, "y": 1, "signal_dbm": -59 }
  ],
  "estimated_source_region": {
    "x": 3,
    "y": 2,
    "zone": "C4",
    "label": "Estimated Source Region",
    "confidence": "MEDIUM",
    "notes": "Visualization estimate only. Indoor RF environments are noisy and multipath effects reduce precision."
  },
  "completed": false,
  "timestamp": "2026-09-18T04:00:00+00:00"
}
```

### POST /api/command
Sends robot command.

Request JSON:

```json
{
  "command": "FORWARD",
  "duration_ms": 500
}
```

Supported commands: `FORWARD`, `BACKWARD`, `LEFT`, `RIGHT`, `STOP`.

Response JSON:

```json
{
  "accepted": true,
  "command": "FORWARD",
  "duration_ms": 500,
  "timestamp": "2026-09-18T04:00:00+00:00"
}
```

Error response (`400`):

```json
{
  "accepted": false,
  "error": "Unsupported command: JUMP"
}
```

## Expected ESP32 Telemetry (Future)

Future ESP32-S3 firmware should post compatible telemetry fields:

- `robot_id` (string)
- `status` (ONLINE/OFFLINE)
- `mode` (IDLE/SCANNING/INVESTIGATING)
- `movement` (FORWARD/BACKWARD/LEFT/RIGHT/STOP)
- `battery` (%)
- `distance_cm` (cm)
- `rssi` (dBm)
- `position.x`, `position.y`, `position.zone`
- `frequency_mhz`, `signal_dbm`, `activity`, `status`
- timestamps in ISO 8601 format

Keeping these names/units stable allows the dashboard to remain unchanged when replacing the simulator with real ESP32 data.
