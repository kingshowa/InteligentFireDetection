# Intelligent Fire Detection System

An intelligent fire detection system that uses computer vision to detect possible fire from a live camera, local video, or online video source, then sends an MQTT alert to an ESP32 device that activates a buzzer and LED warning system.

## Overview

This project combines Python, OpenCV, MQTT communication, and ESP32 hardware to create a real-time fire detection and alert system.

The software application analyzes video frames using color segmentation, motion verification, shape filtering, temporal smoothing, and confidence-based decision logic. When fire is detected, the system displays a warning on the dashboard, logs the event, and sends an MQTT message to an ESP32 device. The ESP32 then activates a buzzer and warning LEDs.

This project demonstrates practical integration between computer vision, desktop UI development, IoT communication, and embedded device control.

## Key Features

- Real-time fire detection from video input
- Supports webcam, local video file, and URL-based video input
- Fire detection using OpenCV-based image processing
- Motion verification to reduce false positives
- Shape analysis and temporal smoothing
- Confidence-based fire detection decision
- Bounding box visualization around detected fire regions
- CustomTkinter dashboard for monitoring video and alerts
- Persistent event logging to CSV
- MQTT communication between Python application and ESP32
- ESP32 buzzer and LED alarm system
- Manual buzzer deactivation from the dashboard
- Threaded video processing for smoother UI operation

## Tech Stack

- **Main Language:** Python
- **Computer Vision:** OpenCV
- **Numerical Processing:** NumPy
- **Desktop UI:** CustomTkinter, Pillow
- **IoT Communication:** MQTT
- **MQTT Broker:** HiveMQ public broker
- **Embedded Device:** ESP32
- **Device Language:** Arduino C++
- **Video Handling:** OpenCV, yt-dlp
- **Event Logging:** CSV
- **Version Control:** Git and GitHub

## Project Structure

```text
InteligentFireDetection/
├── device/
│   └── fireDetectionAlert/
│       └── fireDetectionAlert.ino
├── src/
│   ├── communication/
│   │   └── esp32_client.py
│   ├── detection/
│   │   └── fire_detector.py
│   ├── event_logging/
│   │   └── event_logger.py
│   ├── ui/
│   │   └── dashboard.py
│   ├── video_input/
│   │   └── video_stream.py
│   ├── events_log.csv
│   └── main.py
└── README.md

<img width="1792" height="1024" alt="image" src="https://github.com/user-attachments/assets/7d9511c4-09d9-446d-921c-8b22e95a214c" />
