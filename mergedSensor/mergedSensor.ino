#define BLYNK_TEMPLATE_ID "TMPL6bylgax7L"
#define BLYNK_TEMPLATE_NAME "Sensor Data"
#define BLYNK_AUTH_TOKEN "sXz1_q-z-89Io6eWlEWsFT7OH4k6d1f8"

#include "DHT.h"
#include <WiFi.h>
#include <WiFiClient.h>
#include <BlynkSimpleEsp32.h>

// WiFi credentials
char ssid[] = "Ghost";
char pass[] = "ZakirHall#420";

// --- CJMCU-4541 Pins ---
#define NOX_PIN 34   // NOx analog output
#define RED_PIN 35   // CO analog output
#define PRE_PIN 25   // Preheat pin

// --- Other Sensors ---
#define MQ135_PIN 32      // MQ135 analog input
#define DHTPIN 4          // DHT22 data pin
#define DHTTYPE DHT22
#define FLAME_PIN 27      // Flame Sensor digital

// --- Ultrasonic Sensors ---
#define TRIG1 12
#define ECHO1 14
#define TRIG2 26
#define ECHO2 33
#define TRIG3 18
#define ECHO3 19
#define TRIG4 23
#define ECHO4 5

// --- Objects ---
DHT dht(DHTPIN, DHTTYPE);

// --- CJMCU-4541 parameters ---
const float VCC = 5.0;  // Supply voltage
const float RL = 10.0;  // Load resistance in kOhms
float Ro_NOx = 10.0;    // Baseline (to be calibrated)
float Ro_CO  = 10.0;

// --- Blynk Timer ---
BlynkTimer timer;

// --- Functions ---
float getRs(int adcValue) {
  float voltage = adcValue * (3.3 / 4095.0);
  float Rs = RL * (VCC - voltage) / voltage;
  return Rs;
}

float readUltrasonic(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);
  float distance = duration * 0.034 / 2;
  return distance;
}

bool readFlame() {
  return (digitalRead(FLAME_PIN) == LOW);
}

// --- Send Sensor Data to Blynk ---
void sendSensorData() {
  // CJMCU-4541 NOx/CO
  int noxRaw = analogRead(NOX_PIN);
  int coRaw  = analogRead(RED_PIN);

  float Rs_NOx = getRs(noxRaw);
  float Rs_CO  = getRs(coRaw);

  float ppm_NOx = 100 * (Ro_NOx / Rs_NOx);
  float ppm_CO  = 100 * (Ro_CO / Rs_CO);

  // MQ135
  int mq135Value = analogRead(MQ135_PIN);

  // DHT22
  float hum = dht.readHumidity();
  float temp = dht.readTemperature();

  // Ultrasonics
  float d1 = readUltrasonic(TRIG1, ECHO1);
  float d2 = readUltrasonic(TRIG2, ECHO2);
  float d3 = readUltrasonic(TRIG3, ECHO3);
  float d4 = readUltrasonic(TRIG4, ECHO4);

  // Flame Sensor
  bool flameDetected = readFlame();

  // --- Print to Serial ---
  Serial.println("------ Sensor Data ------");
  Serial.print("NOx: "); Serial.print(ppm_NOx); Serial.println(" ppm");
  Serial.print("CO : "); Serial.print(ppm_CO); Serial.println(" ppm");
  Serial.print("MQ135: "); Serial.println(mq135Value);
  Serial.print("Temp: "); Serial.print(temp); Serial.print(" °C, Hum: "); Serial.print(hum); Serial.println(" %");
  Serial.print("Ultrasonic F: "); Serial.print(d1);
  Serial.print(" cm | L: "); Serial.print(d2);
  Serial.print(" cm | R: "); Serial.print(d3);
  Serial.print(" cm | B: "); Serial.println(d4);
  Serial.print("Flame: "); Serial.println(flameDetected ? "🔥 Detected" : "No Flame");
  Serial.println("-------------------------");

  // --- Send to Blynk ---
  Blynk.virtualWrite(V0, ppm_NOx);  
  Blynk.virtualWrite(V1, ppm_CO);   
  Blynk.virtualWrite(V2, mq135Value);

  if (!isnan(hum) && !isnan(temp)) {
    Blynk.virtualWrite(V3, temp);
    Blynk.virtualWrite(V4, hum);
  }

  Blynk.virtualWrite(V5, d1); // Front
  Blynk.virtualWrite(V6, d2); // Left
  Blynk.virtualWrite(V7, d3); // Right
  Blynk.virtualWrite(V8, d4); // Back
  Blynk.virtualWrite(V9, flameDetected ? 1 : 0);
}

// --- Setup ---
void setup() {
  Serial.begin(115200);

  // WiFi + Blynk
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi Connected");
  Blynk.config(BLYNK_AUTH_TOKEN);
  Blynk.connect();

  // CJMCU-4541 Preheat
  pinMode(PRE_PIN, OUTPUT);
  digitalWrite(PRE_PIN, HIGH);
  analogReadResolution(12); // 0–4095

  // Other sensors
  dht.begin();
  pinMode(FLAME_PIN, INPUT);

  // Ultrasonics
  pinMode(TRIG1, OUTPUT); pinMode(ECHO1, INPUT);
  pinMode(TRIG2, OUTPUT); pinMode(ECHO2, INPUT);
  pinMode(TRIG3, OUTPUT); pinMode(ECHO3, INPUT);
  pinMode(TRIG4, OUTPUT); pinMode(ECHO4, INPUT);

  // Send sensor data every 2 seconds
  timer.setInterval(2000L, sendSensorData);

  Serial.println("✅ ESP32 Sensor Suite connected to Blynk");
}

// --- Loop ---
void loop() {
  Blynk.run();
  timer.run();
}


