#include <Arduino.h>

// Define pins for motor drivers
#define LEFT_IN1 26
#define LEFT_IN2 27
#define LEFT_ENA 14 

#define RIGHT_IN3 25
#define RIGHT_IN4 33
#define RIGHT_ENB 32

// Define pins for RC receiver channels
#define CH1_PIN 4  // Steering (left/right), assuming Channel 1
#define CH2_PIN 5  // Throttle (forward/backward), assuming Channel 2

// PWM properties for ESP32
const int PWM_FREQ = 1000;  // 1kHz PWM frequency
const int PWM_RES = 8;      // 8-bit resolution (0-255)

// Deadzone for sticks to prevent jitter
const int DEADZONE = 20;

// Function to drive a motor
void driveMotor(int in1, int in2, int en, int speed) {
  if (abs(speed) < DEADZONE) {
    speed = 0;
  }
  
  if (speed > 0) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
    ledcWrite(en, abs(speed));
  } else if (speed < 0) {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
    ledcWrite(en, abs(speed));
  } else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
    ledcWrite(en, 0);
  }
}

void setup() {
  // Set pin modes for motor control
  pinMode(LEFT_IN1, OUTPUT);
  pinMode(LEFT_IN2, OUTPUT);
  pinMode(RIGHT_IN3, OUTPUT);
  pinMode(RIGHT_IN4, OUTPUT);
  
  // Set up PWM for ENA and ENB
  ledcAttach(LEFT_ENA, PWM_FREQ, PWM_RES);
  ledcAttach(RIGHT_ENB, PWM_FREQ, PWM_RES);
  
  // Set pin modes for RC inputs
  pinMode(CH1_PIN, INPUT);
  pinMode(CH2_PIN, INPUT);
  
  // Initialize serial for debugging (optional)
  Serial.begin(115200);
}

void loop() {
  // Read pulse widths from RC receiver (timeout 25ms)
  int ch1_raw = pulseIn(CH1_PIN, HIGH, 25000);  // Steering
  int ch2_raw = pulseIn(CH2_PIN, HIGH, 25000);  // Throttle
  
  // If no signal, set to neutral
  if (ch1_raw == 0) ch1_raw = 1500;
  if (ch2_raw == 0) ch2_raw = 1500;
  
  // Map raw PWM values (1000-2000us) to -255 to 255
  int steering = map(ch1_raw, 1000, 2000, -255, 255);
  int throttle = map(ch2_raw, 1000, 2000, -255, 255);
  
  // Clamp values
  steering = constrain(steering, -255, 255);
  throttle = constrain(throttle, -255, 255);
  
  // Mix for tank drive
  int leftSpeed = throttle + steering;
  int rightSpeed = throttle - steering;
  
  // Clamp speeds to valid range
  leftSpeed = constrain(leftSpeed, -255, 255);
  rightSpeed = constrain(rightSpeed, -255, 255);
  
  // Drive motors
  driveMotor(LEFT_IN1, LEFT_IN2, LEFT_ENA, leftSpeed);
  driveMotor(RIGHT_IN3, RIGHT_IN4, RIGHT_ENB, rightSpeed);
  
  // Optional debug output
  // Serial.print("Steering: "); Serial.print(steering);
  // Serial.print(" Throttle: "); Serial.print(throttle);
  // Serial.print(" Left: "); Serial.print(leftSpeed);
  // Serial.print(" Right: "); Serial.println(rightSpeed);
  
  delay(10);  // Small delay for stability
}

