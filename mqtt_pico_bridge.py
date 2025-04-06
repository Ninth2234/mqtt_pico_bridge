import paho.mqtt.client as mqtt
import serial
import time
import json

# MQTT Broker settings
BROKER = "161.200.84.240"  # Example public broker
PORT = 1883
PUBLISH_TOPIC = "pico"
SUBSCRIBE_TOPIC = "pico/control/#"

SERIAL_PORT = "/dev/ttyACM0"  

# Setup Serial connection
ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)

# MQTT setup
client = mqtt.Client()

# Callback function for successful connection
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")
    client.subscribe(SUBSCRIBE_TOPIC)  # Subscribe to the control topic on connection

# Callback function when a message is received
def on_message(client, userdata, msg):
    print(f"Message received on topic {msg.topic}: {msg.payload.decode('utf-8')}")

    subtopic = "/".join(msg.topic.split("/")[2:]).strip()
    payload = msg.payload.decode('utf-8').strip()
    
    if subtopic == "led":
        if payload == "on":
            ser.write(json.dumps({'type':'cmd','cmd':'led','param':{'state':'on'}}).encode())
        if payload == "off":
            ser.write(json.dumps({'type':'cmd','cmd':'led','param':{'state':'off'}}).encode())
        
    
    

# Callback function for message publication
def on_publish(client, userdata, mid):
    ...

# Attach the callback functions
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish

# Connect to MQTT broker
client.connect(BROKER, PORT)

# Start the loop to handle incoming and outgoing MQTT messages
client.loop_start()

try:
    while True:
        serial_data = ser.readline().decode("utf-8").strip()

        if serial_data:

            message_json = json.loads(serial_data)

            msg_type = message_json.get("type")
            if msg_type == "status":

                msg = message_json.get("msg")
                sensor_data = message_json.get("param")

                client.publish(f"{PUBLISH_TOPIC}/{msg}", json.dumps(sensor_data))

            if msg_type == "event":
                event_msg = message_json.get("event")
                client.publish(f"{PUBLISH_TOPIC}/event", json.dumps(event_msg))
                
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Program interrupted")

finally:
    ser.close()  # Close the serial port
    client.loop_stop()  # Stop the MQTT loop
    client.disconnect()  # Disconnect from the MQTT broker
