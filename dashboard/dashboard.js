const API_BASE = "http://127.0.0.1:5000/api";
const signalHistory = [];
const maxSignalPoints = 40;
let latestInvestigation = null;

const stageOrder = ["BASELINE", "SCAN", "DETECT", "MEASURE", "MOVE", "MAP", "LOCALIZE", "ALERT"];
const pipelineContainer = document.getElementById("pipeline");
stageOrder.forEach((stage) => {
  const el = document.createElement("div");
  el.className = "stage";
  el.dataset.stage = stage;
  el.textContent = stage;
  pipelineContainer.appendChild(el);
});

function setDot(id, online) {
  const dot = document.getElementById(id);
  dot.classList.toggle("online", online);
  dot.classList.toggle("offline", !online);
}

function setOfflineState() {
  setDot("backend-dot", false);
  setDot("robot-dot", false);
  setDot("rf-dot", false);
  document.getElementById("robot-online").textContent = "OFFLINE";
}

async function fetchJson(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, options);
  if (!response.ok) {
    throw new Error(`${endpoint} returned ${response.status}`);
  }
  return response.json();
}

function updateRobot(status) {
  document.getElementById("robot-id").textContent = status.robot_id;
  document.getElementById("robot-online").textContent = status.status;
  document.getElementById("robot-mode").textContent = status.mode;
  document.getElementById("robot-movement").textContent = status.movement;
  document.getElementById("robot-battery").textContent = `${status.battery}%`;
  document.getElementById("robot-obstacle").textContent = `${status.distance_cm} cm`;
  document.getElementById("robot-rssi").textContent = `${status.rssi} dBm`;
  document.getElementById("robot-position").textContent = `X ${status.position.x}, Y ${status.position.y}`;
  document.getElementById("robot-zone").textContent = status.position.zone;

  const online = status.status === "ONLINE";
  setDot("robot-dot", online);
}

function updateRf(rf) {
  document.getElementById("rf-status").textContent = rf.status;
  document.getElementById("rf-frequency").textContent = `${rf.frequency_mhz} MHz`;
  document.getElementById("rf-signal").textContent = `${rf.signal_dbm} dBm`;
  document.getElementById("rf-activity").textContent = rf.activity;
  setDot("rf-dot", true);

  signalHistory.push(rf.signal_dbm);
  if (signalHistory.length > maxSignalPoints) signalHistory.shift();
  drawSignalChart();
}

function updateAnomaly(investigation) {
  const anomaly = investigation.anomaly || {};
  document.getElementById("anomaly-description").textContent = anomaly.description || "No anomaly detected.";
  document.getElementById("anomaly-frequency").textContent = anomaly.frequency_mhz ? `${anomaly.frequency_mhz} MHz` : "--";
  document.getElementById("anomaly-signal").textContent = anomaly.signal_dbm ? `${anomaly.signal_dbm} dBm` : "--";
  document.getElementById("anomaly-first-seen").textContent = anomaly.first_seen || "--";
  document.getElementById("anomaly-status").textContent = anomaly.investigation_status || "--";
  document.getElementById("source-label").textContent = investigation.estimated_source_region?.label || "Estimated Source Region";

  document.querySelectorAll(".stage").forEach((node) => {
    node.classList.toggle("active", node.dataset.stage === investigation.stage);
  });
}

function updateEvents(events) {
  const timeline = document.getElementById("timeline");
  timeline.innerHTML = "";
  events
    .slice()
    .reverse()
    .forEach((event) => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${event.message}</strong><br><small>${new Date(event.timestamp).toLocaleTimeString()}</small>`;
      timeline.appendChild(li);
    });
}

function drawSignalChart() {
  const canvas = document.getElementById("signal-chart");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!signalHistory.length) return;

  const min = -90;
  const max = -35;
  const stepX = canvas.width / Math.max(signalHistory.length - 1, 1);

  ctx.strokeStyle = "#26d5ff";
  ctx.lineWidth = 2;
  ctx.beginPath();
  signalHistory.forEach((value, i) => {
    const normalized = (value - min) / (max - min);
    const x = i * stepX;
    const y = canvas.height - normalized * canvas.height;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function drawMap(investigation) {
  const canvas = document.getElementById("map-canvas");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const grid = 7;
  const pad = 20;
  const cell = Math.min((canvas.width - pad * 2) / grid, (canvas.height - pad * 2) / grid);
  const gridWidth = cell * grid;
  const gridHeight = cell * grid;

  ctx.strokeStyle = "#22324e";
  for (let i = 0; i <= grid; i++) {
    const p = pad + i * cell;
    ctx.beginPath();
    ctx.moveTo(pad, p);
    ctx.lineTo(pad + gridWidth, p);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(p, pad);
    ctx.lineTo(p, pad + gridHeight);
    ctx.stroke();
  }

  const points = investigation.measurements || [];
  points.forEach((point, index) => {
    const x = pad + (point.x + 0.5) * cell;
    const y = pad + (point.y + 0.5) * cell;
    const intensity = Math.min(1, Math.max(0, (point.signal_dbm + 80) / 40));

    ctx.fillStyle = `rgba(255, 93, 122, ${0.25 + intensity * 0.6})`;
    ctx.beginPath();
    ctx.arc(x, y, 6, 0, Math.PI * 2);
    ctx.fill();

    if (index > 0) {
      const prev = points[index - 1];
      const px = pad + (prev.x + 0.5) * cell;
      const py = pad + (prev.y + 0.5) * cell;
      ctx.strokeStyle = "#32ffa9";
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(x, y);
      ctx.stroke();
    }
  });

  const robot = points[points.length - 1];
  if (robot) {
    ctx.fillStyle = "#26d5ff";
    ctx.beginPath();
    ctx.arc(pad + (robot.x + 0.5) * cell, pad + (robot.y + 0.5) * cell, 8, 0, Math.PI * 2);
    ctx.fill();
  }

  const estimate = investigation.estimated_source_region;
  if (estimate) {
    const x = pad + (estimate.x + 0.5) * cell;
    const y = pad + (estimate.y + 0.5) * cell;
    ctx.strokeStyle = "#ffc857";
    ctx.lineWidth = 2;
    ctx.strokeRect(x - cell / 2, y - cell / 2, cell, cell);
    ctx.fillStyle = "#ffc857";
    ctx.fillText("Estimated Source Region", x - 42, y - cell / 2 - 6);
  }
}

async function refreshDashboard() {
  try {
    const [status, rf, investigation, events] = await Promise.all([
      fetchJson("/status"),
      fetchJson("/rf"),
      fetchJson("/investigation"),
      fetchJson("/events"),
    ]);

    setDot("backend-dot", true);
    setDot("system-dot", true);
    setDot("camera-dot", false);

    updateRobot(status);
    updateRf(rf);
    updateAnomaly(investigation);
    updateEvents(events);
    drawMap(investigation);
    latestInvestigation = investigation;
  } catch (error) {
    setOfflineState();
    document.getElementById("command-result").textContent = `Backend offline: ${error.message}`;
  }
}

async function sendCommand(command) {
  try {
    const payload = { command, duration_ms: 500 };
    const result = await fetchJson("/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    document.getElementById("command-result").textContent = `${result.command} command accepted`;
    await refreshDashboard();
  } catch (error) {
    document.getElementById("command-result").textContent = `Command failed: ${error.message}`;
  }
}

document.querySelectorAll("#control-panel button").forEach((button) => {
  button.addEventListener("click", () => sendCommand(button.dataset.command));
});

refreshDashboard();
setInterval(refreshDashboard, 1000);
