#include <WiFi.h>

// ============================================================
// CYBER MOSQUITO - NODE 2
// CONTROLLED AP SIMULATION
// ============================================================

const char* NORMAL_SSID = "CYBER-TEST-NODE-2";
const char* ATTACK_SSID = "CYBER-TEST-ATTACK";
const char* AP_PASSWORD = "12345678";

bool attackMode = false;

void startNormalMode() {
  attackMode = false;

  WiFi.softAPdisconnect(true);
  delay(300);

  WiFi.mode(WIFI_AP);

  bool started = WiFi.softAP(
    NORMAL_SSID,
    AP_PASSWORD,
    6,
    false,
    4
  );

  Serial.println();
  Serial.println("========================================");
  Serial.println("NODE 2 - NORMAL");
  Serial.println("========================================");

  Serial.print("AP started: ");
  Serial.println(started ? "YES" : "NO");

  Serial.print("SSID: ");
  Serial.println(NORMAL_SSID);

  Serial.print("BSSID: ");
  Serial.println(WiFi.softAPmacAddress());

  Serial.print("IP: ");
  Serial.println(WiFi.softAPIP());

  Serial.println("CHANNEL: 6");
}

void startAttackSimulation() {
  attackMode = true;

  WiFi.softAPdisconnect(true);
  delay(500);

  WiFi.mode(WIFI_AP);

  bool started = WiFi.softAP(
    ATTACK_SSID,
    AP_PASSWORD,
    11,
    false,
    4
  );

  Serial.println();
  Serial.println("########################################");
  Serial.println("CONTROLLED ATTACK SIMULATION");
  Serial.println("########################################");

  Serial.print("AP started: ");
  Serial.println(started ? "YES" : "NO");

  Serial.print("SSID: ");
  Serial.println(ATTACK_SSID);

  Serial.print("BSSID: ");
  Serial.println(WiFi.softAPmacAddress());

  Serial.println("CHANNEL: 11");
  Serial.println("STATUS: CONTROLLED SIMULATION");
}

void showStatus() {
  Serial.println();
  Serial.println("----------------------------------------");

  Serial.print("MODE: ");
  Serial.println(
    attackMode ? "ATTACK SIMULATION" : "NORMAL"
  );

  Serial.print("SSID: ");
  Serial.println(WiFi.softAPSSID());

  Serial.print("BSSID: ");
  Serial.println(WiFi.softAPmacAddress());

  Serial.print("IP: ");
  Serial.println(WiFi.softAPIP());

  Serial.println("----------------------------------------");
}

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("CYBER MOSQUITO - NODE 2");
  Serial.println("ESP32 CONTROLLED SIMULATION");

  Serial.println();
  Serial.println("N = NORMAL");
  Serial.println("A = ATTACK SIMULATION");
  Serial.println("S = STATUS");

  startNormalMode();
}

void loop() {

  if (Serial.available()) {

    char command = Serial.read();

    if (command == 'N' || command == 'n') {
      startNormalMode();
    }

    else if (command == 'A' || command == 'a') {
      startAttackSimulation();
    }

    else if (command == 'S' || command == 's') {
      showStatus();
    }
  }

  delay(20);
}
