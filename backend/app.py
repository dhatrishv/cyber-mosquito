from __future__ import annotations

from flask import Flask, jsonify, request

from simulator import CyberMosquitoSimulator

app = Flask(__name__)
simulator = CyberMosquitoSimulator()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify(simulator.snapshot()["status"])


@app.route("/api/rf", methods=["GET"])
def get_rf():
    return jsonify(simulator.snapshot()["rf"])


@app.route("/api/events", methods=["GET"])
def get_events():
    return jsonify(simulator.snapshot()["events"])


@app.route("/api/investigation", methods=["GET"])
def get_investigation():
    return jsonify(simulator.snapshot()["investigation"])


@app.route("/api/command", methods=["POST", "OPTIONS"])
def post_command():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    command = str(payload.get("command", "")).upper()
    duration_ms = int(payload.get("duration_ms", 500))
    result = simulator.command(command, duration_ms)

    if not result.get("accepted"):
        return jsonify(result), 400

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
