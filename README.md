# 🧠 FIONA — Field Intelligence and Operational Navigation Assistant

### 🚨 AI-Powered Surveillance and Rescue Robot

FIONA is an **AI-driven surveillance and rescue robot** designed to assist in hazardous environments such as fire zones, industrial accidents, or natural disasters. It intelligently detects injured humans, identifies fire or dangerous gases, evaluates danger levels, and shares GPS coordinates for efficient and safe rescue operations.

---
![WhatsApp Image 2025-10-16 at 16 09 55_9c8ecabd](https://github.com/user-attachments/assets/d422ad63-8e18-4808-a241-8b4d15024168 )
![WhatsApp Image 2025-10-16 at 16 10 37_38737b9d](https://github.com/user-attachments/assets/f522305a-73c1-4f00-9e88-5b5c935dd1c8 )


## 🧩 Table of Contents

* [Overview](#overview)
* [Problem Statement](#problem-statement)
* [Proposed Solution](#proposed-solution)
* [System Architecture](#system-architecture)
* [Features](#features)
* [Technology Stack](#technology-stack)
* [Hardware Components](#hardware-components)
* [Software & AI Models](#software--ai-models)
* [How It Works](#how-it-works)
* [Applications](#applications)
* [Future Improvements](#future-improvements)
* [Team Members](#team-members)

---

## 🔍 Overview

**FIONA (Field Intelligence and Operational Navigation Assistant)** is a smart robot that combines **AI, IoT, and robotics** to support rescue missions and environmental monitoring. It provides real-time analysis of danger zones and autonomously assists operators in decision-making through intelligent perception and data collection.

---

## 🚧 Problem Statement

Rescue operations in disaster zones, industrial sites, and fire-affected areas often expose human rescuers to life-threatening conditions. Traditional surveillance robots only transmit visuals and lack the ability to analyze or classify the surrounding dangers.

---

## 💡 Proposed Solution

FIONA integrates **machine learning, deep learning, and sensor-based data fusion** to autonomously detect injured humans, identify fire and gas presence, assess risk levels, and share GPS coordinates of victims or hazards in real time.

---

## ⚙️ System Architecture

1. **Data Collection:** Environmental data via sensors (Gas, Flame, Temperature, Ultrasonic).
2. **AI Processing:** YOLOv8-based object detection model identifies humans and fire.
3. **Decision Logic:** AI classifies zones into *High*, *Medium*, or *Low* danger levels.
4. **Communication:** Sends alerts, GPS location, and live feed through IoT (Blynk Cloud).
5. **Mobility:** Tank chassis enables smooth movement across rough terrain.

---

## ✨ Features

* 🔥 Fire and gas detection
* 🧍 Human and injured person detection (YOLO-based AI)
* 📍 Real-time GPS tracking
* ☁️ IoT cloud dashboard via Blynk
* 📡 Live data streaming to operators
* ⚠️ Danger-level classification (Low, Medium, High)
* 🪖 Tank-based chassis for rough environments

---

## 🧠 Technology Stack

| Category                  | Technologies                                                    |
| ------------------------- | --------------------------------------------------------------- |
| **AI Model**              | YOLOv8 (Object Detection)                                       |
| **Microcontroller**       | ESP32                                                           |
| **Cloud Platform**        | Blynk IoT                                                       |
| **Programming Languages** | Python, C++                                                     |
| **Sensors**               | Gas Sensor, Flame Sensor, Temperature Sensor, Ultrasonic Sensor |
| **Connectivity**          | Wi-Fi, GPS Module                                               |
| **Power**                 | 4× 3.7V Li-ion Batteries                                        |
| **Hardware Base**         | Tank Chassis with Dual Gear Motors                              |

---

## 🤖 Software & AI Models

* **YOLOv8 Model:** Detects humans and fires in real time.
* **ESP32 Control Logic:** Handles sensor data and communication.
* **Blynk Dashboard:** Displays live readings, GPS location, and alerts.
* **AI Processing Unit (Raspberry Pi):** Runs ML/DL inference and decision support.

---

## 🔄 How It Works

1. **Robot scans** the environment using camera and sensors.
2. **YOLOv8 model** processes live video to detect humans or fire.
3. **Sensors** collect temperature, gas, and flame data.
4. **Danger levels** are calculated based on AI and sensor data.
5. **GPS module** sends location to the operator dashboard.
6. **Blynk IoT** displays the status, alerts, and live data remotely.

---

## 🏭 Applications

* Firefighter support and rescue operations
* Military surveillance in risky terrains
* Industrial accident monitoring
* Smart lab safety automation
* Disaster recovery missions

---

## 🚀 Future Improvements

* Integration with thermal cameras
* Autonomous pathfinding with AI-based SLAM
* Two-way communication (voice alerts)
* Drone-assisted overhead mapping

---

## 👥 Team Members

| Name                   | Role                                       |
| ---------------------- | ------------------------------------------ |
| **Samiul Sazid Sammo** | Hardware Design & IoT Integration |
| **Al Shahria Hasan Shawon**    | Software Development        |

---

## 🏁 Conclusion

FIONA represents the fusion of **AI, IoT, and Robotics** in one intelligent system designed to **save lives, reduce risks, and enhance situational awareness** during emergencies. It’s not just a robot — it’s a **field assistant for the future of rescue operations.**
