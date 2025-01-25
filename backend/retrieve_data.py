import paho.mqtt.client as mqtt
import requests
from flask import Flask, jsonify, abort
from flask_cors import CORS 
import threading
from datetime import datetime, timedelta
import os


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


# MQTT setup
broker = "broker.hivemq.com"
sensor_topic = "home/raspberrypi/sensor"
motor_topic = "home/raspberrypi/motor"

temperature = None
humidity = None
client = None
motor_start_file = "motor_last_started.txt"  # File to store the last motor start date

@app.route('/api/motor/<command>', methods=['POST'])
def action_motor(command):
    if command not in ['start', 'stop']:
        # If the command is not valid, return a 400 Bad Request
        abort(400, description="Invalid command. Use 'start_motor' or 'stop_motor'.")

    # Publish the command to the motor topic using MQTT
    if command == 'start':
        client.publish(motor_topic, "start_motor")
        print("Motor start command sent.")
    elif command == 'stop':
        client.publish(motor_topic, "stop_motor")
        print("Motor stop command sent.")

    # Return a success response
    return jsonify({"message": f"{command} command sent"}), 200


@app.route('/api/sensor', methods=['GET'])
def get_sensor_data():
    # Return temperature and humidity as JSON
    return jsonify({
        "temperature": temperature,
        "humidity": humidity
    })


@app.route('/api/weather', methods=['GET'])
def get_weather():
    url = f"http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}"
    params = {"apikey": api_key,
              "metric": "true"}
    response = requests.get(url, params=params)
                    
    if response.status_code == 200:
        data = response.json()
        daily_forecasts = data["DailyForecasts"]
        #print(daily_forecasts)
        return data
    else:
        print("Failed to get weather forecast ")
        print(response)
        return []

# Load the last motor start date from file (if exists)
def load_motor_start_date():
    if os.path.exists(motor_start_file):
        with open(motor_start_file, 'r') as file:
            date_str = file.read().strip()
            if date_str:
                return datetime.strptime(date_str, "%Y-%m-%d")
    return None

# Save the current date as the motor start date
def save_motor_start_date():
    with open(motor_start_file, 'w') as file:
        file.write(datetime.now().strftime("%Y-%m-%d"))

# Get the last motor start date
last_motor_start = load_motor_start_date()

def read_api_key(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()  # Strip any leading/trailing whitespace

# AccuWeather API setup
api_key = read_api_key("apikey.txt")
location_key = 287713  # Cluj-Napoca location id


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(sensor_topic)

def on_message(client, userdata, msg):
    #print(f"Message received: {msg.topic} {msg.payload.decode()}")
    global temperature, humidity, last_motor_start
    payload = msg.payload.decode()

    try:
        temp_str, hum_str = payload.split(";")
        temperature = float(temp_str.split(": ")[1].split(" ")[0])
        humidity = float(hum_str.split(": ")[1].replace("%", ""))
        print(f"Stored Temperature: {temperature} C")
        print(f"Stored Humidity: {humidity} %")
        if humidity <= 40:
            print("Humidity <= 40%: Checking weather forecast...")
            forecast = check_weather_forecast()
            if forecast:
                print(f"It will rain in {forecast} days in Cluj-Napoca")
            else:
                if last_motor_start and (datetime.now() - last_motor_start < timedelta(days=5)):
                    print(f"Plants have been watered on {last_motor_start.strftime('%Y-%m-%d')}.")
                else:
                    client.publish(motor_topic, "start_motor")
                    save_motor_start_date() #save current date
                    last_motor_start = datetime.now() # update last start
                    print("No rain in the next 3 days: Signal sent to start the water pump")
    except Exception as e:
        print(f"Error parsing message: {e}")
    
# Function to check weather forecast
def check_weather_forecast():
    url = f"http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}"
    params = {"apikey": api_key,
              "metric": "true"}
    response = requests.get(url, params=params)
                    
    if response.status_code == 200:
        data = response.json()
        daily_forecasts = data["DailyForecasts"]
        #print(daily_forecasts)

        # Check the next 3 days for rain
        for i in range(3):
            day = daily_forecasts[i]
            if day["Day"]["HasPrecipitation"] and day["Day"]["PrecipitationType"] == "Rain":
                return i + 1  # Return the day number (1-based index)

        # No rain in the next 3 days
        return None
    else:
        #print(response)
        print("Failed to get weather forecast")
        return None


def run_mqtt():
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, 1883, 60) #default port, plain tcp used; keep-alive in s
    client.loop_forever()

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    mqtt_thread = threading.Thread(target=run_mqtt)

    # Start both threads
    flask_thread.start()
    mqtt_thread.start()

    # Wait for both threads to complete (they will run forever)
    flask_thread.join()
    mqtt_thread.join()
