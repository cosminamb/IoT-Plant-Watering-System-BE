#import the libraries
import RPi.GPIO as GPIO
import Adafruit_DHT
import pigpio

import paho.mqtt.client as mqtt
import time

#SENSOR
GPIO.setmode(GPIO.BCM)
#name the type of sensor used
type = Adafruit_DHT.DHT11
#declare the pin used by the sensor in GPIO form
dht11 = 25
#set the sensor as INPUT
GPIO.setup(dht11, GPIO.IN)

#SERVO
pi = pigpio.pi()
#store the pin used by the servo
servo = 18
#set the pin as OUTPUT
pi.set_mode(18, pigpio.OUTPUT)



#MQTT setup
broker = "broker.hivemq.com" #public broker
sensor_topic = "home/raspberrypi/sensor"
motor_topic = "home/raspberrypi/motor"


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(motor_topic)

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print("Received message " + payload)
    if payload == "start_motor":
        #put the servo in the position of 90 degrees
        pi.set_servo_pulsewidth(servo, 1000)
        #sleep 1 second
        time.sleep(0.3)
        #put the servo in the position of 0 degrees
        pi.set_servo_pulsewidth(servo, 2000)
        print()
        
#create MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, 1883, 60)
client.loop_start()

#Read the values and print them in terminal
try:
 while True:
     #make the reading
     humidity, temperature = Adafruit_DHT.read_retry(type, dht11)
     #we will display the values only if they are not null
     if humidity is not None and temperature is not None:
         print('Temperature = {:.1f} Humidity ={:.1f}' .format(temperature, humidity))
         payload = f"Temp: {temperature:.2f} C;Humidity: {humidity:.2f}%"
         client.publish(sensor_topic, payload)
         print("Published: " + payload)
         print()
except KeyboardInterrupt:
    #stop the servo pulses
    pi.set_servo_pulsewidth(servo, 0)
    #stop the connection with the daemon
    pi.stop()
    
#clean all the used ports
GPIO.cleanup()