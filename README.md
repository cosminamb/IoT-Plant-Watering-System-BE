# IoT-Plant-Watering-System-BE

This project involves a Raspberry Pi with a temperature and humidity sensor and a motor, and a Python backend application that communicates with the Raspberry Pi via MQTT. The system monitors the environmental conditions and controls a motor based on the humidity level and weather forecast.

#### Key Components:

1. **Raspberry Pi Sensor Setup**:
   - A Python script (`temperature.py`) runs on the Raspberry Pi, reading temperature and humidity values from the sensor and publishing them to an MQTT broker (`broker.hivemq.com`) on topic `home/raspberrypi/sensor`.

2. **Backend Server**:
   - A Flask-based Python backend subscribes to the sensor's MQTT `home/raspberrypi/sensor` topic, processes the data, and publishes control signals for the motor based on specified conditions.
   - The backend checks if the humidity drops below 40% and, if so, fetches the weather forecast for the next three days from the AccuWeather API.
   - If no rain is forecasted, it sends a "start_motor" message via MQTT to start the motor connected to the Raspberry Pi. The motor represent a water pump that is triggered to water the plants.
   - Backend module exposes RESTful API endpoints:
     - `GET /api/sensor`: Returns the current temperature and humidity values.
     - `POST /api/motor/{command}`: Controls the motor (start/stop).
     - `GET /api/weather`: Calls AccuWeather API and returns the forecast for the next 5 days for a specific location.   


#### Workflow:
- The Raspberry Pi reads sensor data and publishes it to the MQTT broker.
- The backend subscribes to the sensor data and, based on humidity levels and weather forecast, controls a motor connected to the Raspberry Pi via MQTT.
- Users can view sensor data and send motor control commands through the frontend.
