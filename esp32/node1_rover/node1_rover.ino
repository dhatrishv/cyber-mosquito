#include <WiFi.h>
#include <HTTPClient.h>

// ============================================================
// CYBER MOSQUITO - NODE 1 ROVER
// WIFI SCANNER + TELEMETRY + MOTOR CONTROL
// ============================================================

// ---------- CHANGE THESE ----------
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

const char* BACKEND_HOST = "192.168.1.20";
const int BACKEND_PORT = 8000;
// ---------------------------------

const char* TARGET_SSID = "CYBER-TEST-ATTACK";

// Safe, configurable motor pins.
// Do NOT use GPIO 6/7 on classic ESP32 flash-connected boards.
#define LEFT_IN1   18
#define LEFT_IN2   19
#define RIGHT_IN1  21
#define RIGHT_IN2  22

const unsigned long SCAN_INTERVAL = 5000;
const unsigned long TELEMETRY_INTERVAL = 2500;

int channelActivity[14];

bool targetDetected = false;
int targetRSSI = -100;
int targetChannel = -1;
int networkCount = 0;

String roverState = "STARTING";
String directionState = "STOPPED";
bool moving = false;
String lastEvent = "System starting";

unsigned long bootMillis;
unsigned long lastScan = 0;
unsigned long lastTelemetry = 0;

// ============================================================
// MOTOR
// ============================================================

void stopMotors() {
  digitalWrite(LEFT_IN1, LOW);
  digitalWrite(LEFT_IN2, LOW);
  digitalWrite(RIGHT_IN1, LOW);
  digitalWrite(RIGHT_IN2, LOW);

  moving = false;
  directionState = "STOPPED";
  roverState = "STOPPED";
}

void forward() {
  digitalWrite(LEFT_IN1, HIGH);
  digitalWrite(LEFT_IN2, LOW);
  digitalWrite(RIGHT_IN1, HIGH);
  digitalWrite(RIGHT_IN2, LOW);

  moving = true;
  directionState = "FORWARD";
  roverState = "MANUAL";
}

void backward() {
  digitalWrite(LEFT_IN1, LOW);
  digitalWrite(LEFT_IN2, HIGH);
  digitalWrite(RIGHT_IN1, LOW);
  digitalWrite(RIGHT_IN2, HIGH);

  moving = true;
  directionState = "BACKWARD";
  roverState = "MANUAL";
}

void leftTurn() {
  digitalWrite(LEFT_IN1, LOW);
  digitalWrite(LEFT_IN2, HIGH);
  digitalWrite(RIGHT_IN1, HIGH);
  digitalWrite(RIGHT_IN2, LOW);

  moving = true;
  directionState = "LEFT";
  roverState = "MANUAL";
}

void rightTurn() {
  digitalWrite(LEFT_IN1, HIGH);
  digitalWrite(LEFT_IN2, LOW);
  digitalWrite(RIGHT_IN1, LOW);
  digitalWrite(RIGHT_IN2, HIGH);

  moving = true;
  directionState = "RIGHT";
  roverState = "MANUAL";
}

// ============================================================
// SCAN
// ============================================================

void scanWiFi() {

  targetDetected = false;
  targetRSSI = -100;
  targetChannel = -1;

  for (int i = 0; i < 14; i++) {
    channelActivity[i] = 0;
  }

  roverState = "SCANNING";

  int result = WiFi.scanNetworks(false, true);

  if (result < 0) {
    lastEvent = "Wi-Fi scan failed";
    roverState = "ERROR";
    return;
  }

  networkCount = result;

  for (int i = 0; i < result; i++) {

    String ssid = WiFi.SSID(i);
    int rssi = WiFi.RSSI(i);
    int channel = WiFi.channel(i);

    if (channel >= 1 && channel <= 13) {
      channelActivity[channel]++;
    }

    if (ssid == TARGET_SSID) {

      if (!targetDetected || rssi > targetRSSI) {
        targetDetected = true;
        targetRSSI = rssi;
        targetChannel = channel;
      }
    }

    delay(2);
  }

  WiFi.scanDelete();

  if (targetDetected) {
    lastEvent = "Controlled attack simulation detected";
    roverState = "THREAT DETECTED";
  } else {
    lastEvent = "RF scan complete - target absent";
    roverState = "SEARCHING";
    stopMotors();
  }
}

// ============================================================
// TELEMETRY JSON
// ============================================================

String telemetryJSON() {

  unsigned long uptime =
    (millis() - bootMillis) / 1000;

  String json = "{";

  json += "\"rover\":{";
  json += "\"online\":true,";
  json += "\"state\":\"" + roverState + "\",";
  json += "\"direction\":\"" + directionState + "\",";
  json += "\"moving\":" + String(moving ? "true" : "false");
  json += "},";

  json += "\"rf\":{";
  json += "\"targetDetected\":" +
          String(targetDetected ? "true" : "false") + ",";
  json += "\"targetSSID\":\"" + String(TARGET_SSID) + "\",";
  json += "\"targetRSSI\":" + String(targetRSSI) + ",";
  json += "\"targetChannel\":" + String(targetChannel) + ",";
  json += "\"networkCount\":" + String(networkCount) + ",";
  json += "\"threatType\":\"" +
          String(targetDetected ? "CONTROLLED SIMULATION" : "NONE") +
          "\",";

  json += "\"channels\":[";
  for (int i = 1; i <= 13; i++) {
    json += String(channelActivity[i]);
    if (i < 13) json += ",";
  }
  json += "]";
  json += "},";

  json += "\"system\":{";
  json += "\"uptime\":" + String(uptime) + ",";
  json += "\"lastEvent\":\"" + lastEvent + "\",";
  json += "\"lastSeen\":" + String(millis() / 1000);
  json += "}";

  json += "}";

  return json;
}

// ============================================================
// SEND TELEMETRY
// ============================================================

void sendTelemetry() {

  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;

  String url =
    "http://" +
    String(BACKEND_HOST) +
    ":" +
    String(BACKEND_PORT) +
    "/api/telemetry";

  http.begin(url);
  http.addHeader(
    "Content-Type",
    "application/json"
  );

  String payload = telemetryJSON();

  int code = http.POST(payload);

  Serial.print("[HTTP] telemetry: ");
  Serial.println(code);

  http.end();
}

// ============================================================
// COMMANDS FROM BACKEND
// ============================================================

void handleSerialCommand() {

  if (!Serial.available()) return;

  char c = Serial.read();

  if (c == 'F' || c == 'f') {
    forward();
  }

  else if (c == 'B' || c == 'b') {
    backward();
  }

  else if (c == 'L' || c == 'l') {
    leftTurn();
  }

  else if (c == 'R' || c == 'r') {
    rightTurn();
  }

  else if (c == 'S' || c == 's') {
    stopMotors();
  }
}

// ============================================================
// SIMPLE HTTP COMMAND SERVER
// Uses WiFiServer rather than WebServer to keep firmware small.
// ============================================================

WiFiServer commandServer(80);

void checkCommandServer() {

  WiFiClient client = commandServer.available();

  if (!client) return;

  unsigned long start = millis();

  while (
    client.connected() &&
    millis() - start < 300
  ) {

    if (client.available()) {

      String line = client.readStringUntil('\n');

      if (line.indexOf("/cmd?c=F") >= 0) forward();
      else if (line.indexOf("/cmd?c=B") >= 0) backward();
      else if (line.indexOf("/cmd?c=L") >= 0) leftTurn();
      else if (line.indexOf("/cmd?c=R") >= 0) rightTurn();
      else if (line.indexOf("/cmd?c=S") >= 0) stopMotors();

      break;
    }

    delay(1);
  }

  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/plain");
  client.println("Connection: close");
  client.println();
  client.println("OK");

  client.stop();
}

// ============================================================
// SETUP
// ============================================================

void setup() {

  Serial.begin(115200);
  delay(2500);

  Serial.println();
  Serial.println("========================================");
  Serial.println("CYBER MOSQUITO - NODE 1 ROVER");
  Serial.println("========================================");

  // Motors
  pinMode(LEFT_IN1, OUTPUT);
  pinMode(LEFT_IN2, OUTPUT);
  pinMode(RIGHT_IN1, OUTPUT);
  pinMode(RIGHT_IN2, OUTPUT);

  stopMotors();

  Serial.println("[OK] Motors initialized");

  // Wi-Fi
  WiFi.mode(WIFI_STA);

  WiFi.begin(
    WIFI_SSID,
    WIFI_PASSWORD
  );

  Serial.print("Connecting Wi-Fi");

  unsigned long start = millis();

  while (
    WiFi.status() != WL_CONNECTED &&
    millis() - start < 15000
  ) {
    delay(250);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {

    Serial.println("[OK] Wi-Fi connected");

    Serial.print("Node 1 IP: ");
    Serial.println(WiFi.localIP());

    commandServer.begin();

  } else {

    Serial.println("[ERROR] Wi-Fi connection failed");
    roverState = "OFFLINE";
  }

  bootMillis = millis();

  scanWiFi();

  sendTelemetry();

  lastScan = millis();
  lastTelemetry = millis();

  Serial.println("SYSTEM READY");
}

// ============================================================
// LOOP
// ============================================================

void loop() {

  handleSerialCommand();

  checkCommandServer();

  if (
    millis() - lastScan >=
    SCAN_INTERVAL
  ) {

    lastScan = millis();

    scanWiFi();
  }

  if (
    millis() - lastTelemetry >=
    TELEMETRY_INTERVAL
  ) {

    lastTelemetry = millis();

    sendTelemetry();
  }

  delay(5);
}
