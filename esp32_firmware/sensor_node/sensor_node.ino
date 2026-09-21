/*
  ESP32 Sensor Node — Encroachment Detection Project

  Reads PIR motion, HC-SR04 ultrasonic distance, and SW-420 vibration,
  and serves them as JSON over Wi-Fi at:

      GET http://<ESP32_IP>/sensors

  Response format matches exactly what the Python side expects:
      {"pir": true, "distance_cm": 182.4, "vibration": 1.0}

  Also exposes:
      POST http://<ESP32_IP>/alert   -> sounds buzzer + LED for 1.5s
*/

#include <WiFi.h>
#include <WebServer.h>

// ---- YOUR WIFI CREDENTIALS (already filled in) ----
const char* ssid = "_GAT_";
const char* password = "rach@123";
// ----------------------------------------------------

#define PIR_PIN 27
#define TRIG_PIN 5
#define ECHO_PIN 18
#define VIBRATION_PIN 26
#define BUZZER_PIN 4
#define LED_PIN 15

WebServer server(80);

float readDistanceCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30ms timeout (~5m max range)
  if (duration == 0) {
    return -1; // no echo received -- out of range or nothing reflecting
  }
  return duration * 0.0343 / 2.0; // convert to cm using speed of sound
}

void handleSensors() {
  bool pir = digitalRead(PIR_PIN) == HIGH;
  bool vibration = digitalRead(VIBRATION_PIN) == HIGH;
  float distance = readDistanceCM();

  String json = "{";
  json += "\"pir\":" + String(pir ? "true" : "false") + ",";
  json += "\"distance_cm\":" + (distance < 0 ? String("null") : String(distance, 1)) + ",";
  json += "\"vibration\":" + String(vibration ? 1.0 : 0.0);
  json += "}";

  server.send(200, "application/json", json);
}

void handleAlert() {
  digitalWrite(BUZZER_PIN, HIGH);
  digitalWrite(LED_PIN, HIGH);
  delay(1500);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  server.send(200, "text/plain", "alert triggered");
}

void handleRoot() {
  server.send(200, "text/plain", "ESP32 sensor node is running. Try GET /sensors");
}

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nFAILED to connect. Check your SSID/password and try again.");
    return;
  }

  Serial.println();
  Serial.print("Connected! ESP32 IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println("Open this in a browser to test: http://" + WiFi.localIP().toString() + "/sensors");

  server.on("/", handleRoot);
  server.on("/sensors", handleSensors);
  server.on("/alert", HTTP_POST, handleAlert);
  server.begin();
  Serial.println("HTTP server started.");
}

void loop() {
  server.handleClient();
}
