"""
Device 1: Smart Building Environmental Sensor Node
"""

import paho.mqtt.client as mqtt
import time
import random
import json
from datetime import datetime

BROKER_HOST = "192.168.12.100"
BROKER_PORT = 1883
USERNAME = "104385170"
PASSWORD = "104385170"

# Topics
PRIVATE_TOPIC = "104385170/building/sensors"
PUBLIC_PUB_TOPIC = "public/104385170/building/status"
COMMAND_TOPIC = "104385170/building/commands"
PUBLIC_SUB_TOPIC = "public/#"

sensor_state = {
    "alarm_active": False,
    "sensor_reset": False,
}

PUBLISH_INTERVAL = 5


def generate_sensor_data():
    return {
        "device_id": "ENV-SENSOR-01",
        "location": "Building E / Floor 4",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": round(random.uniform(20.0, 30.0), 2),
        "humidity": round(random.uniform(40.0, 70.0), 2),
        "co2_ppm": random.randint(400, 1200),
        "alarm_active": sensor_state["alarm_active"],
    }


def generate_public_status(data):
    return {
        "device_id": "ENV-SENSOR-01",
        "location": "Building A / Floor 2",
        "timestamp": data["timestamp"],
        "status": "ALARM" if data["alarm_active"] else "NORMAL",
    }


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[Device 1] Connected to MQTT broker successfully.")

        client.subscribe(COMMAND_TOPIC)
        print(f"[Device 1] Subscribed to command topic: {COMMAND_TOPIC}")

        # COMMENTED PUBLIC SUBSCRIBE FOR CLEANER OUTPUT
        # client.subscribe(PUBLIC_SUB_TOPIC)

    else:
        print(f"[Device 1] Connection failed. Return code: {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8", errors="replace")

    if topic == COMMAND_TOPIC:

        print(f"\n[Device 1] COMMAND RECEIVED")
        print(f"Payload: {payload}")

        try:
            cmd = json.loads(payload)
            action = cmd.get("action", "").lower()

            if action == "trigger_alarm":
                sensor_state["alarm_active"] = True

                print("[Device 1] Alarm is now ON")

            elif action == "reset_sensor":
                sensor_state["alarm_active"] = False
                sensor_state["sensor_reset"] = True

                print("[Device 1] Sensor reset successful")
                print("[Device 1] Alarm is now OFF")

            elif action == "status_check":

                status = "ON" if sensor_state["alarm_active"] else "OFF"

                print(f"[Device 1] Current Alarm Status: {status}")

            else:
                print("[Device 1] Unknown command")

        except json.JSONDecodeError:
            print("[Device 1] Invalid JSON payload")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[Device 1] Unexpected disconnection (rc={rc}).")


def main():

    client = mqtt.Client(client_id="ENV-SENSOR-01")

    client.username_pw_set(USERNAME, PASSWORD)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print("=" * 60)
    print("SMART BUILDING SENSOR DEVICE")
    print("=" * 60)

    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    except Exception as e:
        print(f"Connection error: {e}")
        return

    client.loop_start()

    try:
        while True:

            data = generate_sensor_data()

            private_payload = json.dumps(data)

            client.publish(PRIVATE_TOPIC, private_payload, qos=1)

            print(f"\n[PRIVATE] Published Sensor Data")
            print(f"Temperature : {data['temperature']} °C")
            print(f"Humidity    : {data['humidity']} %")
            print(f"CO2         : {data['co2_ppm']} ppm")

            if data["alarm_active"]:
                print("Alarm Status: ON")
            else:
                print("Alarm Status: OFF")

            public_payload = json.dumps(generate_public_status(data))

            client.publish(PUBLIC_PUB_TOPIC, public_payload, qos=0)

            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print("\n[Device 1] Shutting down...")

    finally:
        client.loop_stop()
        client.disconnect()
        print("[Device 1] Disconnected.")


if __name__ == "__main__":
    main()