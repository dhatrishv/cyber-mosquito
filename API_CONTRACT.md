# API Contract

Base URL:

`http://<BACKEND_IP>:8000`

## GET /api/health

Returns:

```json
{"ok":true}
```

## GET /api/telemetry

Returns the latest Node 1 state:

```json
{
  "rover": {
    "online": true,
    "state": "SEARCHING",
    "direction": "RIGHT",
    "moving": true
  },
  "rf": {
    "targetDetected": true,
    "targetSSID": "CYBER-TEST-ATTACK",
    "targetRSSI": -48,
    "targetChannel": 11,
    "networkCount": 17,
    "channels": [2,0,1,0,0,4,0,0,1,0,5,0,1],
    "threatType": "CONTROLLED SIMULATION"
  },
  "system": {
    "uptime": 1234,
    "lastEvent": "Controlled attack simulation detected",
    "lastSeen": 1710000000
  }
}
```

## POST /api/telemetry

Node 1 posts the same structure. Backend stores the latest state.

## POST /api/rover/command

Request:

```json
{"command":"F"}
```

Commands:

- `F` forward
- `B` backward
- `L` left
- `R` right
- `S` stop

The backend forwards the command to Node 1 when `NODE1_COMMAND_URL` is configured.

## GET /api/events

Returns recent events.

## POST /api/events

Request:

```json
{"message":"Example event","level":"INFO"}
```
